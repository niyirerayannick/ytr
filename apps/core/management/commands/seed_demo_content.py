import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.about.models import BeliefPoint, CallTimelineEntry, SevenMountain
from apps.accounts.models import PrayerRequest, Profile, Testimony
from apps.articles.models import Article, Author
from apps.core.models import Gathering, SiteSettings
from apps.devotions.models import Devotion
from apps.faq.models import FAQ
from apps.library.models import Book
from apps.podcasts.models import Episode, PodcastSeries
from apps.videos.models import Video, VideoSeries

User = get_user_model()


class Command(BaseCommand):
    help = "Loads the sample content from the ytr.html prototype into the database."

    def handle(self, *args, **options):
        self.seed_site_settings()
        self.seed_gathering()
        self.seed_devotions()
        self.seed_articles()
        self.seed_podcasts()
        self.seed_videos()
        self.seed_books()
        self.seed_mountains()
        self.seed_beliefs()
        self.seed_timeline()
        self.seed_faqs()
        self.seed_demo_accounts()
        self.stdout.write(self.style.SUCCESS("Demo content seeded successfully."))

    # ------------------------------------------------------------- accounts
    def seed_demo_accounts(self):
        author_user, created = User.objects.get_or_create(
            username="author_demo", defaults={"email": "author_demo@youthtimerevival.rw", "is_active": True},
        )
        if created:
            author_user.set_password("demo-pass-123")
            author_user.save()
        author_user.profile.role = Profile.ROLE_AUTHOR
        author_user.profile.save()

        member_user, created = User.objects.get_or_create(
            username="member_demo", defaults={"email": "member_demo@youthtimerevival.rw", "is_active": True},
        )
        if created:
            member_user.set_password("demo-pass-123")
            member_user.save()
        member_user.profile.role = Profile.ROLE_MEMBER
        member_user.profile.save()

        # An unapproved sign-up, so the admin "pending sign-ups" queue has something to show.
        pending_user, created = User.objects.get_or_create(
            username="pending_demo", defaults={"email": "pending_demo@youthtimerevival.rw", "is_active": False},
        )
        if created:
            pending_user.set_password("demo-pass-123")
            pending_user.save()

        # A draft + a pending-review article from the demo author, so the admin
        # "pending content" queue and the author dashboard both have something to show.
        Article.objects.update_or_create(
            slug="walking-in-the-daylight",
            defaults=dict(
                title_en="Walking in the Daylight", title_rw="Kugenda mu Mucyo",
                hook_en="A draft in progress — not yet submitted for review.",
                hook_rw="Umushinga ukiri gukorwa — utarohererezwa kugenzurwa.",
                body_en="This is a work in progress.", body_rw="Iki ni igikorwa gikiri mu nzira.",
                author=None, icon="wave", color="#1E6E71",
                status=Article.STATUS_DRAFT, submitted_by=author_user,
            ),
        )
        Article.objects.update_or_create(
            slug="the-weight-of-small-obedience",
            defaults=dict(
                title_en="The Weight of Small Obedience", title_rw="Uburemere bw'Ubwumvikane Buto",
                hook_en="Nobody claps for the small decisions, but they're the ones that hold everything up.",
                hook_rw="Nta muntu wishimira ibyemezo bito, ariko ni byo bishyigikira byose.",
                body_en=(
                    "Nobody builds a testimony around the times they told the truth when a lie "
                    "would have been easier, or showed up when it would have been easier not to.\n\n"
                    "But that is exactly the material a life of integrity is made from."
                ),
                body_rw=(
                    "Nta muntu wubaka ubuhamya ku bihe yavuze ukuri mu gihe ikinyoma cyari "
                    "cyoroshye, cyangwa yahagereye mu gihe byari byoroshye kutahagera.\n\n"
                    "Ariko icyo ni cyo gikoresho nyacyo ubuzima bw'ubunyangamugayo bwubakwaho."
                ),
                author=None, icon="heart", color="#544A6C",
                status=Article.STATUS_PENDING, submitted_by=author_user, submitted_at=timezone.now(),
            ),
        )

        # A pending testimony and an unreviewed prayer request from the demo member.
        Testimony.objects.get_or_create(
            member=member_user, title="Found my two evenings",
            defaults={"body": "I started keeping Wednesday and Sunday evenings for prayer this year, and it changed everything about how I carry the rest of my week."},
        )
        PrayerRequest.objects.get_or_create(
            member=member_user,
            defaults={"body": "Please pray for my family as we go through a difficult season."},
        )
        self.stdout.write("Demo accounts ready (author_demo / member_demo / pending_demo, password demo-pass-123).")

    # ---------------------------------------------------------------- core
    def seed_site_settings(self):
        settings = SiteSettings.load()
        settings.contact_email = "hello@youthtimerevival.rw"
        settings.mission_en = (
            "To build hearts on fire for God — raising a generation rooted in prayer, "
            "taught in truth, and sent into every sphere of society."
        )
        settings.mission_rw = (
            "Kubaka imitima yaka umuriro ku bw'Imana — kurera umuryango ushinze imizi "
            "mu isengesho, wigishijwe ukuri, kandi wohererejwe mu bice byose by'imibereho."
        )
        settings.vision_en = (
            "A generation that carries the presence of God from the altar into politics, "
            "education, health, finance, media, security, and entertainment — until revival "
            "is normal, not rare."
        )
        settings.vision_rw = (
            "Umuryango utwara ubuhorane bw'Imana uva ku gicaniro ujya muri politiki, "
            "uburezi, ubuzima, imari, itangazamakuru, umutekano, n'imyidagaduro — kugeza "
            "ubuzima bushya buba ibisanzwe, atari gake."
        )
        settings.save()
        self.stdout.write("Site settings ready.")

    def seed_gathering(self):
        start = timezone.make_aware(datetime.datetime.combine(
            self._next_friday(), datetime.time(18, 0)
        ))
        end = start + datetime.timedelta(hours=2)
        Gathering.objects.update_or_create(
            title="YTR Fellowship Gathering",
            defaults=dict(
                description="Worship, teaching, open prayer, and time to be known.",
                location="Altar of Prayer — Kigali, Rwanda",
                start_datetime=start,
                end_datetime=end,
                recurring=True,
            ),
        )
        self.stdout.write("Gathering ready.")

    @staticmethod
    def _next_friday():
        today = timezone.localdate()
        days_ahead = (4 - today.weekday()) % 7  # Monday=0 ... Friday=4
        days_ahead = days_ahead or 7
        return today + datetime.timedelta(days=days_ahead)

    # ------------------------------------------------------------ devotions
    def seed_devotions(self):
        today = timezone.localdate()
        data = [
            dict(
                date=today, verse_ref="Psalm 46:10", is_featured=True,
                verse_text_en="Be still — stop striving long enough to remember who is actually in control.",
                verse_text_rw="Ba amahoro — reka kwihatira gato, wibuke neza uwo ari we ufite ubuyobozi.",
                reflection_en=(
                    "Most of what wears us out isn't the work itself — it's carrying what was "
                    "never ours to carry. The altar is where we put it down. Not because the "
                    "outcome no longer matters, but because Someone else is already holding it. "
                    "Stillness is not passivity; it's a decision to stop managing what God has "
                    "already promised to manage."
                ),
                reflection_rw=(
                    "Ibituruhisha akenshi si umurimo ubwawo — ni uko dukomeza kwikorera ibyo "
                    "tutigeze duhabwa kwikorera. Igicaniro n'aho tubishyira hasi. Ntabwo ari uko "
                    "ibizava muri byo bitakiri ngombwa, ahubwo ni uko hari undi umaze kubifata "
                    "neza. Kuba amahoro ntabwo ari ukudakora ikintu — ni ugufata icyemezo cyo "
                    "kureka kuyobora ibyo Imana isanzwe yasezeranyije kuyobora."
                ),
                prayer_en="Prayer: Lord, what I am carrying that You never asked me to carry, I put it down now. Be God over it. Amen.",
                prayer_rw="Isengesho: Mwami, ibyo nikoreye kandi utambwiye kubikorera, ndabishyize hasi none. Ba Imana kuribyo. Amen.",
            ),
            dict(
                date=today - datetime.timedelta(days=2), verse_ref="John 15:4 — Remain", is_featured=False,
                verse_text_en="Fruit is not something you produce. It's something that happens while you stay.",
                verse_text_rw="Imbuto si ikintu wikorera. Ni ikintu kiba mu gihe ugumye.",
                reflection_en="Fruit is not something you produce. It's something that happens while you stay.",
                reflection_rw="Imbuto si ikintu wikorera. Ni ikintu kiba mu gihe ugumye.",
                prayer_en="Prayer: Lord, teach me to remain. Amen.",
                prayer_rw="Isengesho: Mwami, nyigisha kuguma muri Wowe. Amen.",
            ),
            dict(
                date=today - datetime.timedelta(days=4), verse_ref="1 Kings 19:12 — The Quiet Voice", is_featured=False,
                verse_text_en="God was not in the wind or the fire. He was in the whisper. Don't chase the noise.",
                verse_text_rw="Imana ntiyari mu muyaga cyangwa mu muriro. Yari mu ijwi ryoroheje. Ntukurikire urusaku.",
                reflection_en="God was not in the wind or the fire. He was in the whisper. Don't chase the noise.",
                reflection_rw="Imana ntiyari mu muyaga cyangwa mu muriro. Yari mu ijwi ryoroheje. Ntukurikire urusaku.",
                prayer_en="Prayer: Lord, quiet my heart to hear You. Amen.",
                prayer_rw="Isengesho: Mwami, tuza umutima wanjye kugira ngo nkumve ijwi ryawe. Amen.",
            ),
            dict(
                date=today - datetime.timedelta(days=7), verse_ref="Proverbs 4:23 — Guard Your Heart", is_featured=False,
                verse_text_en="Everything you build flows from one place. Guard it before you build anything else.",
                verse_text_rw="Ibyo wubaka byose bikomoka ahantu hamwe. Harinde mbere yo kubaka ikindi cyose.",
                reflection_en="Everything you build flows from one place. Guard it before you build anything else.",
                reflection_rw="Ibyo wubaka byose bikomoka ahantu hamwe. Harinde mbere yo kubaka ikindi cyose.",
                prayer_en="Prayer: Lord, guard my heart above all else. Amen.",
                prayer_rw="Isengesho: Mwami, rinda umutima wanjye mbere ya byose. Amen.",
            ),
        ]
        for entry in data:
            Devotion.objects.update_or_create(
                date=entry["date"],
                defaults={**entry, "status": Devotion.STATUS_PUBLISHED, "published_at": timezone.now()},
            )
        self.stdout.write("Devotions ready.")

    # ------------------------------------------------------------- articles
    def seed_articles(self):
        author, _ = Author.objects.get_or_create(
            name="Youth Time Revival Team",
            defaults=dict(
                bio_en="Reflections from the YTR community, drawn from teaching shared at our gatherings.",
                bio_rw="Ibitekerezo biva mu muryango wa YTR, bivuye mu nyigisho zasangiwe mu materaniro yacu.",
            ),
        )

        articles = [
            dict(
                slug="not-in-the-masses", icon="flame", color="#241A3D", is_featured=True,
                title_en="Not in the Masses", title_rw="Ntibiri mu Bwinshi bw'Abantu",
                hook_en="The altar that changed everything wasn't in a crowd. It was in a room, alone, twice a week.",
                hook_rw="Igicaniro cyahinduye byose ntabwo cyari mu bwinshi bw'abantu. Cyari mu cyumba, wenyine, kabiri mu cyumweru.",
                body_en="\n\n".join([
                    "There is a kind of faith that only survives in a crowd. Take away the music, the lights, and the people standing next to you, and it has nothing left to stand on. That is not the faith we are being built for.",
                    "Revival did not begin in a stadium. It began in a room set apart — an appointment kept twice a week, when no one was watching and nothing was being performed. Two ordinary evenings became an altar, and the altar became a habit, and the habit became a life.",
                    "This is the invitation underneath everything Youth Time Revival does: before the platform, the altar. Before the sermon, the secret place. Before you are sent to any mountain — politics, education, media, finance — you are first built in a room nobody applauds.",
                    "If your faith only works in public, it isn't finished being built yet. Start again this week. Find your two evenings. Show up even when it is only you and God.",
                ]),
                body_rw="\n\n".join([
                    "Hari ukwizera gushobora kubaho gusa iyo uri mu bantu benshi. Ukuvanyeho umuziki, itara, n'abantu bakuri iruhande, ntacyo gusigaramo. Ni ukwizera dukurikira, ntabwo ari ko.",
                    "Ubuzima bushya ntibwatangiye mu iteraniro rinini. Bwatangiriye mu cyumba cyihariye — igihe cyagenwe kabiri mu cyumweru, nta muntu ureba kandi nta kintu cyerekanwa. Amajoro abiri asanzwe yabaye igicaniro, igicaniro kiba akamenyero, akamenyero kaba ubuzima.",
                    "Iyi niyo ntumira iri munsi y'ibindi byose Youth Time Revival ikora: mbere y'urwuri, igicaniro. Mbere y'ubutumwa, ahantu hihishwa. Mbere yo koherezwa ku musozi uwo ari wo wose — politiki, uburezi, itangazamakuru, imari — ubanza kubakwa mu cyumba nta muntu uguhamagarira.",
                    "Niba ukwizera kwawe gukora gusa mu bantu benshi, ntabwo kurangiye kubakwa. Tangira ubu kuriyi cyumweru. Shaka amajoro yawe abiri. Ujye uhagera n'igihe uri wenyine na Imana gusa.",
                ]),
                verse_text_en="Jesus taught His followers to pray in a private room, with the door shut, where only the Father sees.",
                verse_text_rw="Yesu yigishije abigishwa be gusenga mu cyumba cy'ibanga, umuryango ufunze, aho Se wo mu ijuru gusa arebera.",
                verse_ref_en="Matthew 6:6 (paraphrased)", verse_ref_rw="Matayo 6:6 (byasobanuwe)",
            ),
            dict(
                slug="fire-that-doesnt-go-out", icon="flame", color="#7A2E17", is_featured=False,
                title_en="The Fire That Doesn't Go Out", title_rw="Umuriro Udazima",
                hook_en="Every revival fades unless someone tends the coals. Revival is not an event we attend — it's a fire we feed.",
                hook_rw="Ubuzima bushya bwose burazima keretse hari ubukomeza kubungabunga amakara. Ubuzima bushya si igikorwa tugiyeho — ni umuriro tugomba kongera inkwi.",
                body_en="\n\n".join([
                    "It's easy to confuse a moment for a movement. A gathering can feel like revival for one night and be forgotten by the following week, because nobody went home and kept the coals warm.",
                    "The three pillars of the altar — prayer, faith, and the Holy Spirit — were never meant to be a memory of what happened once. They are daily maintenance. A fire needs feeding, not admiring.",
                    "So the question isn't 'did God move at the gathering?' It's 'what did you do on Tuesday, when nobody was watching, to keep the fire alive?' That's where revival either continues or quietly goes out.",
                ]),
                body_rw="\n\n".join([
                    "Biroroshye guhindura akanya kamwe ngo bibe umuvuko wose. Iteraniro rishobora kumva ari ubuzima bushya ijoro rimwe, hanyuma ryibagirana mu cyumweru gikurikira, kubera ko nta wagarutse murugo akomeza gushyushya amakara.",
                    "Inkingi eshatu z'igicaniro — isengesho, ukwizera, n'Umwuka Wera — ntibyigeze bigenewe kuba urwibutso rw'ikintu cyabaye rimwe. Ni umurimo wa buri munsi. Umuriro ukeneye inkwi, ntabwo ari ukuwureba gusa.",
                    "Bityo, ikibazo si 'Imana yakoze iki mu materaniro?' Ni 'wakoze iki ku wa gatatu, igihe nta wari ureba, kugira ngo ukomeze umuriro?' Aho niho ubuzima bushya bukomereza cyangwa bugatuza buhoro buhoro.",
                ]),
                verse_text_en="Quench not the Spirit.", verse_text_rw="Ntimukazimye Umwuka w'Imana.",
                verse_ref_en="1 Thessalonians 5:19 (KJV)", verse_ref_rw="1 Abatesalonike 5:19 (Bibiliya Yera)",
            ),
            dict(
                slug="sent-not-hidden", icon="mountain", color="#1E6E71", is_featured=False,
                title_en="Sent, Not Hidden", title_rw="Twoherejwe, Ntitwihishe",
                hook_en="God did not call this generation to hide in a holy corner. He called it to seven ordinary mountains.",
                hook_rw="Imana ntiyahamagariye uyu muryango kwihisha mu nguni yera. Yawohereje ku misozi irindwi isanzwe.",
                body_en="\n\n".join([
                    "There is a version of faith that retreats — that treats the world outside the church building as too dangerous to enter. That was never the assignment.",
                    "Politics, entertainment, education, health, finance, security, communication and media — these are not enemy territory to avoid. They are the seven places this generation is being sent, carrying not a slogan, but a changed life.",
                    "A city on a hill cannot be hidden. If revival stays inside a room, it was never finished — it was only started.",
                ]),
                body_rw="\n\n".join([
                    "Hari ubwoko bw'ukwizera busubira inyuma — bufata isi hanze y'itorero nk'ahantu hakomeye cyane ho kwinjiramo. Ntabwo ari ko byari byagenwe.",
                    "Politiki, imyidagaduro, uburezi, ubuzima, imari, umutekano, itangazamakuru — ntabwo ari intara y'umwanzi wo kwirinda. Ni ahantu hirindwi uyu muryango woherejwemo, utwaye atari ijambo ryo ku munwa gusa, ahubwo ubuzima buhindutse.",
                    "Umujyi uri ku musozi ntushobora guhishwa. Niba ubuzima bushya bugumira mu cyumba, ntibwari burarangiye kubakwa — bwari butangiye gusa.",
                ]),
                verse_text_en="You are the light of the world; a city on a hill cannot be hidden.",
                verse_text_rw="Uri umucyo w'isi; umujyi uri ku musozi ntushobora guhishwa.",
                verse_ref_en="Matthew 5:14 (paraphrased)", verse_ref_rw="Matayo 5:14 (byasobanuwe)",
            ),
            dict(
                slug="faith-without-an-audience", icon="flame", color="#7A2E17", is_featured=False,
                title_en="Faith Without an Audience", title_rw="Ukwizera Nta Bareba",
                hook_en="The version of you that shows up when no one is watching is the only version God is actually building.",
                hook_rw="Uwo uri we igihe nta muntu ureba, ni we Imana ikirimo kubaka by'ukuri.",
                body_en="\n\n".join([
                    "Every generation is tempted by the same lie: that faith which is seen is faith that counts. But the altar was never designed for an audience.",
                    "What you do when the room is empty — the prayer nobody claps for, the obedience nobody photographs — is the actual material God is shaping. Public faith is just private faith finally showing.",
                    "So stop auditioning. The secret place isn't a waiting room before the real thing starts. It is the real thing.",
                ]),
                body_rw="\n\n".join([
                    "Buri gisekuru kirakorwa n'ikinyoma kimwe: ukwizera kugaragara ni ko kubarwa. Ariko igicaniro ntabwo cyigeze cyubakwa kugira ngo kigaragarizwe abantu.",
                    "Ibyo ukora igihe icyumba kidafite abantu — isengesho nta uwaryishimira, ubwumvikane nta uwabufotora — ni byo Imana ikoresha by'ukuri mu kugukora. Ukwizera kugaragara ni ukwizera kw'ibanga kumaze kugaragazwa.",
                    "Reka rero kwigereranya n'abandi. Ahantu hihishwa ntabwo ari icyumba cyo gutegereza mbere y'ikintu nyakuri. Ni cyo kintu nyakuri ubwacyo.",
                ]),
                verse_text_en="But when you pray, go into your room, close the door, and pray to your Father, who is unseen.",
                verse_text_rw="Ariko iyo usenga, injira mu cyumba cyawe, ufunge umuryango, hanyuma usengere Se wawe utaboneka.",
                verse_ref_en="Matthew 6:6", verse_ref_rw="Matayo 6:6",
            ),
            dict(
                slug="the-quiet-voice", icon="river", color="#1E6E71", is_featured=False,
                title_en="The Quiet Voice", title_rw="Ijwi Ryoroheje",
                hook_en="God was not in the wind, the earthquake, or the fire. Most of us are still waiting by the wrong window.",
                hook_rw="Imana ntiyari mu muyaga, mu mutingito, cyangwa mu muriro. Benshi muri twe turacyategereje idirishya ritari ryo.",
                body_en="\n\n".join([
                    "Elijah expected God to arrive the way power usually arrives — loud, dramatic, undeniable. Instead, after the wind and the fire had passed, there was a whisper. That was where God actually was.",
                    "We have built a generation that chases noise — bigger gatherings, louder testimonies, faster answers. But the pattern in Scripture is consistent: God prefers the whisper to the spectacle.",
                    "If your life has gone quiet lately, that is not necessarily absence. Lean in. The instruction was never to wait for the fire. It was to listen for the whisper.",
                ]),
                body_rw="\n\n".join([
                    "Eliya yari yiteze ko Imana izaza uko imbaraga zisanzwe ziza — mu rusaku, mu bitangaza, mu buryo budashidikanywaho. Ahubwo, umuyaga n'umuriro byararangiye, haza ijwi ryoroheje. Aho ni ho Imana yari iri by'ukuri.",
                    "Twarubatse umuryango ukurikirana urusaku — amateraniro manini, ubuhamya burenga, ibisubizo byihuse. Ariko uko Ibyanditswe bibivuga ntibihinduka: Imana ikunda ijwi ryoroheje kuruta ibitangaza.",
                    "Niba ubuzima bwawe bwabaye buto muri iki gihe, ntabwo ari uko Imana itariho. Tega amatwi. Itegeko ntabwo ryari ryo gutegereza umuriro. Ni ugutega amatwi ijwi ryoroheje.",
                ]),
                verse_text_en="And after the fire came a gentle whisper.",
                verse_text_rw="Umuriro urangiye, haza ijwi ryoroheje.",
                verse_ref_en="1 Kings 19:12", verse_ref_rw="1 Abami 19:12",
            ),
            dict(
                slug="mentorship-is-not-a-meeting", icon="cap", color="#C24A24", is_featured=False,
                title_en="Mentorship Is Not a Meeting", title_rw="Ubuyobozi Hafi Ntabwo ari Inama",
                hook_en="You cannot download character. Someone has to walk close enough for you to watch how they carry it.",
                hook_rw="Imico ntishobora kwigishwa gusa mu magambo. Hakenewe umuntu ugenda hafi yawe ukareba uko ayitwara.",
                body_en="\n\n".join([
                    "A lot of what we call mentorship is really just information transfer — a talk, a book recommendation, a quote shared once. Real mentorship is proximity over time.",
                    "The disciples didn't learn from Jesus in a single lecture. They watched Him pray, watched Him get tired, watched Him respond to people who didn't deserve kindness. Formation happens at close range.",
                    "If you want to grow, stop collecting content and start asking someone to let you close. And if you're further along, someone is waiting for you to open the door.",
                ]),
                body_rw="\n\n".join([
                    "Byinshi twita ubuyobozi hafi, ni ukwimura amakuru gusa — ijambo rimwe, igitabo cyasabwe, umugani wasangiwe rimwe. Ubuyobozi hafi nyakuri ni ukuba hafi mu gihe kirekire.",
                    "Abigishwa ntibigiye kuri Yesu mu nyigisho imwe gusa. Barebaga uko asenga, barebaga uko ananirwa, barebaga uko asubiza abantu batari bakwiye ubuntu. Imico irahindurwa iyo uri hafi.",
                    "Niba ushaka gukura, reka gukusanya amakuru gusa, ubwira umuntu ngo akwegereze hafi ye. Kandi niba warimaze urugendo, hari umuntu utegereje ko ufungura umuryango.",
                ]),
                verse_text_en="Whoever walks with the wise becomes wise.",
                verse_text_rw="Ugenda n'abanyabwenge azaba umunyabwenge.",
                verse_ref_en="Proverbs 13:20 (paraphrased)", verse_ref_rw="Imigani 13:20 (byasobanuwe)",
            ),
            dict(
                slug="guarding-what-you-build", icon="shield", color="#544A6C", is_featured=False,
                title_en="Guarding What You Build", title_rw="Kurinda Icyo Wubaka",
                hook_en="Everything you build overflows from your heart. Protect the source before you protect the structure.",
                hook_rw="Ibyo wubaka byose bikomoka ku mutima wawe. Rinda isoko mbere yo kurinda inyubako.",
                body_en="\n\n".join([
                    "We spend enormous energy protecting our reputation, our platform, our plans — and very little protecting the actual place all of it comes from.",
                    "Scripture doesn't say guard your calendar or guard your image. It says guard your heart, because everything else is downstream of it.",
                    "So before you build the next thing, ask what is happening in the hidden place. A cracked source will eventually show up in the structure, no matter how good the structure looks from outside.",
                ]),
                body_rw="\n\n".join([
                    "Dukoresha imbaraga nyinshi kurinda izina ryacu, urwuri rwacu, imigambi yacu — ariko tukarinda gato ahantu ibyo byose bikomokaho.",
                    "Ibyanditswe ntibivuga ngo rinda gahunda yawe cyangwa ishusho yawe. Bivuga ngo rinda umutima wawe, kuko ibindi byose bikomoka aho.",
                    "Bityo, mbere yo kubaka ikindi kintu, ibaze icyo kiba muri wowe wihishe. Isoko yamenetse izagaragara mu nyubako, uko iyo nyubako yaba yiza ite iyo ureba hanze.",
                ]),
                verse_text_en="Above all else, guard your heart, for everything you do flows from it.",
                verse_text_rw="Kurusha ibindi byose, rinda umutima wawe, kuko aho ni ho ibyo ukora byose bikomoka.",
                verse_ref_en="Proverbs 4:23", verse_ref_rw="Imigani 4:23",
            ),
            dict(
                slug="money-without-a-master", icon="coin", color="#F6B93B", is_featured=False,
                title_en="Money Without a Master", title_rw="Amafaranga Adafite Shebuja",
                hook_en="Money makes a good servant and a cruel master. The altar is where you decide which one it will be.",
                hook_rw="Amafaranga ni umukozi mwiza ariko ni shebuja ukatiye. Igicaniro ni aho uhitamo icyo azaba kuri wowe.",
                body_en="\n\n".join([
                    "Nobody plans to be owned by money. It happens quietly — one compromise, one anxious decision, one late night calculating what you're worth by what you have.",
                    "Stewardship isn't a budgeting technique. It's a daily declaration that everything in your hand belongs to Someone else, and you are simply managing it well for a season.",
                    "If you want to know who's really in charge — you or your bank account — watch how you respond the next time it drops. That reaction will tell you the truth.",
                ]),
                body_rw="\n\n".join([
                    "Nta muntu ugena kuzaba igikoresho cy'amafaranga. Biba buhoro buhoro — kwemera ikintu kimwe, icyemezo cyo guhangayika, ijoro ryo kubara agaciro kawe ukurikije icyo ufite.",
                    "Ubugenzuzi si uburyo bwo gukora ingengo y'imari gusa. Ni ukwemeza buri munsi ko ibyo ufite byose ari iby'undi, kandi wowe uba ubiyobora neza gusa mu gihe runaka.",
                    "Niba ushaka kumenya uwafata ubuyobozi by'ukuri — wowe cyangwa konti yawe — reba uko uzitwara igihe izagabanuka. Icyo gisubizo kizakubwira ukuri.",
                ]),
                verse_text_en="You cannot serve both God and money.",
                verse_text_rw="Ntushobora gukorera Imana n'amafaranga icyarimwe.",
                verse_ref_en="Matthew 6:24 (paraphrased)", verse_ref_rw="Matayo 6:24 (byasobanuwe)",
            ),
            dict(
                slug="seven-mountains-one-altar", icon="mountain", color="#241A3D", is_featured=False,
                title_en="Seven Mountains, One Altar", title_rw="Imisozi Irindwi, Igicaniro Kimwe",
                hook_en="You don't need seven altars for seven mountains. You need one altar that's strong enough to send you to all seven.",
                hook_rw="Ntugomba kugira ibicaniro birindwi ku misozi irindwi. Ukeneye igicaniro kimwe gikomeye gishobora kukwohereza kuri iyo yose.",
                body_en="\n\n".join([
                    "It's tempting to think politics needs one kind of spirituality, business another, and ministry a third. But the altar that forms you doesn't change by address.",
                    "The same secret place that shapes a pastor also shapes a teacher, a nurse, a civil servant, an artist. What changes is the mountain you're sent to — not the room you were built in.",
                    "So don't wait until you reach 'your' mountain to start building the altar. Build it now, wherever you are, and let it send you wherever you're needed.",
                ]),
                body_rw="\n\n".join([
                    "Birashobora kumva ko politiki ikeneye ubwoko bumwe bw'ubuzima bw'umwuka, ubucuruzi ubundi, n'umurimo w'ubutumwa ubundi. Ariko igicaniro cyagukoze ntabwo gihinduka ukurikije aho uri.",
                    "Ahantu hihishwa hamwe hagenera pasitori niho hagenera umwarimu, umuforomo, umukozi wa Leta, n'umuhanzi. Icyahinduka ni umusozi woherezwaho — atari icyumba wubakiwemo.",
                    "Bityo, ntutegereze kugera ku musozi wawe kugira ngo utangire kubaka igicaniro. Kibake ubu, aho uri hose, ukireke kikohereze aho ukenewe hose.",
                ]),
                verse_text_en="Go and make disciples of all nations.",
                verse_text_rw="Nimugende mwigishe amahanga yose.",
                verse_ref_en="Matthew 28:19 (paraphrased)", verse_ref_rw="Matayo 28:19 (byasobanuwe)",
            ),
            dict(
                slug="when-the-fire-feels-distant", icon="flame", color="#E4572E", is_featured=False,
                title_en="When the Fire Feels Distant", title_rw="Igihe Umuriro Wumva Ukure",
                hook_en="Dry seasons are not proof God left. Sometimes they're proof the altar has stopped being decoration and started being discipline.",
                hook_rw="Ibihe by'ubwumye ntabwo ari ikimenyetso cy'uko Imana yagiye. Rimwe na rimwe ni ikimenyetso cy'uko igicaniro kitakiri icyo kuranga gusa ahubwo cyabaye umuco.",
                body_en="\n\n".join([
                    "Every person who has kept an altar for any length of time hits a season where it feels like talking to a ceiling. That season is not a malfunction — it's part of the process.",
                    "Feelings were never the fuel of the altar. Faithfulness is. The evenings you show up dry are worth more than the ones where everything feels alive, because they prove you didn't come for the feeling.",
                    "Keep the appointment anyway. The whisper you're waiting for usually arrives after the season you wanted to quit in, not before it.",
                ]),
                body_rw="\n\n".join([
                    "Buri muntu wabungabunze igicaniro igihe kirekire agera ku gihe umva nk'uvugana n'urusenge. Icyo gihe si ikibazo — ni igice cy'urugendo.",
                    "Uruhame ntabwo rwigeze ruba inkwi z'igicaniro. Ubudahemuka ni bwo bwa ngombwa. Amajoro uhagerera ukumva uyumye afite agaciro kurusha ay'uko byose byumva bifite ubuzima, kuko agaragaza ko utazanywe n'uruhame.",
                    "Komeza igihe cyagenwe uko byaba byose. Ijwi ryoroheje utegereje akenshi riza nyuma y'igihe wumvaga ushaka kureka, atari mbere yaho.",
                ]),
                verse_text_en="Let us not become weary in doing good, for at the proper time we will reap a harvest if we do not give up.",
                verse_text_rw="Ntiducogore gukora icyiza, kuko igihe cyagenwe tuzasarura tutaruhutse.",
                verse_ref_en="Galatians 6:9", verse_ref_rw="Abagalatiya 6:9",
            ),
        ]

        base_time = timezone.now()
        for i, data in enumerate(articles):
            slug = data.pop("slug")
            Article.objects.update_or_create(
                slug=slug,
                defaults=dict(
                    author=author,
                    status=Article.STATUS_PUBLISHED,
                    published_at=base_time - datetime.timedelta(days=i * 3),
                    **data,
                ),
            )
        self.stdout.write("Articles ready.")

    # ------------------------------------------------------------- podcasts
    def seed_podcasts(self):
        series_data = [
            dict(
                slug="kanguka", icon="mic", color="#E4572E", order=0,
                title_en="Kanguka", title_rw="Kanguka",
                subtitle_en="The wake-up call series", subtitle_rw="Urukurikirane rwo gukangura",
                description_en="Short, direct episodes meant to interrupt spiritual sleep — start here if you're new to YTR.",
                description_rw="Ibiganiro bigufi, bigaragara neza, bigenewe guhagarika ibitotsi byo mu buryo bw'umwuka — tangirira hano niba uri mushya muri YTR.",
                episodes=[
                    dict(title_en="Wake Up First", title_rw="Banza Ukangurwe",
                         description_en="Why revival always starts with one honest person, not a crowd.",
                         description_rw="Impamvu ubuzima bushya butangirira ku muntu umwe wumva ukuri, atari ku bwinshi.",
                         duration="11 min"),
                    dict(title_en="You Are Not Behind", title_rw="Ntabwo Urengejwe",
                         description_en="Comparing your calling to someone else's timeline will cost you the fire.",
                         description_rw="Kugereranya ihamagara ryawe n'iry'undi bizagutwara umuriro wawe.",
                         duration="9 min"),
                    dict(title_en="Small Rooms, Big Moves", title_rw="Ibyumba Bito, Ibikorwa Bikomeye",
                         description_en="Why God prefers to start things where no one is filming.",
                         description_rw="Impamvu Imana ikunda gutangirira ahantu nta muntu ufata amashusho.",
                         duration="13 min"),
                ],
            ),
            dict(
                slug="altar-talks", icon="flame", color="#1E6E71", order=1,
                title_en="Altar Talks", title_rw="Ibiganiro by'Igicaniro",
                subtitle_en="Conversations on prayer & the secret place", subtitle_rw="Ibiganiro ku isengesho n'ahantu hihishwa",
                description_en="Longer conversations on building and keeping a personal life of prayer.",
                description_rw="Ibiganiro birebire ku kubaka no kubungabunga ubuzima bwite bw'isengesho.",
                episodes=[
                    dict(title_en="Building Your Two Evenings", title_rw="Kubaka Amajoro Yawe Abiri",
                         description_en="A practical conversation on setting apart real time with God.",
                         description_rw="Ikiganiro gifatika ku kugena igihe nyacyo cyo kubana n'Imana.",
                         duration="24 min"),
                    dict(title_en="When Prayer Feels Dry", title_rw="Igihe Isengesho Ryumva Ryumye",
                         description_en="What to do in seasons when the altar feels quiet.",
                         description_rw="Icyo gukora mu bihe igicaniro cyumva gituje.",
                         duration="19 min"),
                    dict(title_en="Faith As A Pillar", title_rw="Ukwizera Nk'Inkingi",
                         description_en="Why faith is a pillar of the altar, not just a feeling.",
                         description_rw="Impamvu ukwizera ari inkingi y'igicaniro, atari uruhame gusa.",
                         duration="21 min"),
                ],
            ),
            dict(
                slug="mountain-conversations", icon="mountain", color="#F6B93B", order=2,
                title_en="Mountain Conversations", title_rw="Ibiganiro by'Imisozi",
                subtitle_en="Interviews across the seven mountains", subtitle_rw="Ibiganiro mu misozi irindwi",
                description_en="Young believers talk about following Christ inside politics, health, media, and more.",
                description_rw="Urubyiruko rwizera ruvuga ku gukurikira Kristo muri politiki, ubuzima, itangazamakuru, n'ibindi.",
                episodes=[
                    dict(title_en="Faith in the Classroom", title_rw="Ukwizera mu Ishuri",
                         description_en="A young teacher on integrity in the education mountain.",
                         description_rw="Umwarimu w'umusore avuga ku bunyangamugayo mu musozi w'uburezi.",
                         duration="27 min"),
                    dict(title_en="Money Without an Idol", title_rw="Amafaranga Adafite Igishushanyo",
                         description_en="A conversation on stewardship in the finance mountain.",
                         description_rw="Ikiganiro ku bugenzuzi mu musozi w'imari.",
                         duration="22 min"),
                    dict(title_en="Camera On, Heart Steady", title_rw="Kamera Ikanze, Umutima Ugumye",
                         description_en="A media creator on staying grounded in the entertainment mountain.",
                         description_rw="Umukozi wo mu itangazamakuru avuga ku kuguma ushinze imizi mu musozi w'imyidagaduro.",
                         duration="18 min"),
                ],
            ),
        ]

        for data in series_data:
            slug = data.pop("slug")
            episodes = data.pop("episodes")
            series, _ = PodcastSeries.objects.update_or_create(slug=slug, defaults=data)
            for i, ep in enumerate(episodes):
                Episode.objects.update_or_create(
                    series=series, title_en=ep["title_en"],
                    defaults=dict(order=i, status=Episode.STATUS_PUBLISHED, published_at=timezone.now(), **ep),
                )
        self.stdout.write("Podcasts ready.")

    # -------------------------------------------------------------- videos
    def seed_videos(self):
        series_data = [
            dict(slug="sunday", color="#241A3D", order=0, title_en="Sunday Gatherings", title_rw="Amateraniro y'Icyumweru",
                 videos=[("The Altar Life", "Ubuzima bw'Igicaniro"), ("Faith As A Pillar", "Ukwizera Nk'Inkingi"), ("Sent to Seven Mountains", "Twoherejwe ku Misozi Irindwi")]),
            dict(slug="testimonies", color="#7A2E17", order=1, title_en="Testimonies", title_rw="Ubuhamya",
                 videos=[("From the Back Row", "Uvuye Inyuma"), ("A Year of Fridays", "Umwaka w'Ukuwagatanu"), ("Still Standing", "Ndacyahagaze")]),
            dict(slug="altarnights", color="#1E6E71", order=2, title_en="Altar Nights", title_rw="Amajoro y'Igicaniro",
                 videos=[("Friday Prayer, Full Room", "Isengesho ry'Ukuwatanu"), ("Waiting Without Noise", "Gutegereza Nta Rusaku"), ("The Whisper", "Ijwi Ryoroheje")]),
        ]
        first = True
        for data in series_data:
            slug = data.pop("slug")
            videos = data.pop("videos")
            series, _ = VideoSeries.objects.update_or_create(slug=slug, defaults=data)
            for i, (title_en, title_rw) in enumerate(videos):
                Video.objects.update_or_create(
                    series=series, title_en=title_en,
                    defaults=dict(
                        title_rw=title_rw, order=i, is_featured=first and i == 0,
                        status=Video.STATUS_PUBLISHED, published_at=timezone.now(),
                    ),
                )
            first = False
        self.stdout.write("Videos ready.")

    # -------------------------------------------------------------- library
    def seed_books(self):
        books = [
            dict(title_en="Bibiliya Yera (The Bible)", title_rw="Bibiliya Yera", icon="book", color="#241A3D",
                 description_en="Scripture, the foundation of everything YTR teaches.",
                 description_rw="Ibyanditswe Byera, urufatiro rw'ibyo YTR yigisha byose.",
                 external_link="https://www.bible.com", link_label_en="Read online", link_label_rw="Soma kuri interineti"),
            dict(title_en="Indirimbo z'Ukwizera (Hymn Book)", title_rw="Indirimbo z'Ukwizera", icon="flame", color="#E4572E",
                 description_en="Hymns sung at the altar and in fellowship gatherings.",
                 description_rw="Indirimbo ziririmbwa ku gicaniro no mu materaniro y'ubusabane."),
            dict(title_en="Umugenzi", title_rw="Umugenzi", icon="mountain", color="#1E6E71",
                 description_en="The Kinyarwanda translation of a classic on the Christian journey.",
                 description_rw="Igitabo cy'ubuzima bw'ukwizera cyahinduwe mu Kinyarwanda."),
            dict(title_en="Imbuto z'Umwuka (Fruit of the Spirit)", title_rw="Imbuto z'Umwuka", icon="river", color="#F6B93B",
                 description_en="A short discipleship guide on character shaped by the Spirit.",
                 description_rw="Igitabo gito cyo kwigisha imico igenwa n'Umwuka."),
            dict(title_en="Amasengesho y'Igicaniro (Altar Prayers)", title_rw="Amasengesho y'Igicaniro", icon="flame", color="#7A2E17",
                 description_en="YTR's own collection of prayers for the personal altar.",
                 description_rw="Amasengesho YTR yateguye ku bw'igicaniro bwite."),
            dict(title_en="Ubuzima bw'Umuyoboke (Life of a Disciple)", title_rw="Ubuzima bw'Umuyoboke", icon="book", color="#544A6C",
                 description_en="A mentorship handbook for small-group leaders.",
                 description_rw="Igitabo cy'ubuyobozi ku bayobozi b'amatsinda mato."),
        ]
        for i, data in enumerate(books):
            Book.objects.update_or_create(title_en=data["title_en"], defaults=dict(order=i, **{k: v for k, v in data.items() if k != "title_en"}))
        self.stdout.write("Books ready.")

    # ------------------------------------------------------------ mountains
    def seed_mountains(self):
        mountains = [
            dict(icon="gavel", name_en="Politics", name_rw="Politiki",
                 description_en="Raising leaders shaped by integrity, not ambition.",
                 description_rw="Kurera abayobozi bashinze imizi mu bunyangamugayo."),
            dict(icon="mask", name_en="Entertainment", name_rw="Imyidagaduro",
                 description_en="Reflecting beauty and creativity, not just noise.",
                 description_rw="Kwerekana ubwiza n'ubushobozi, atari urusaku gusa."),
            dict(icon="cap", name_en="Education", name_rw="Uburezi",
                 description_en="Teaching wisdom, not only information.",
                 description_rw="Kwigisha ubwenge, atari amakuru gusa."),
            dict(icon="heart", name_en="Health", name_rw="Ubuzima",
                 description_en="Whole-person wellbeing rooted in God.",
                 description_rw="Ubuzima bwuzuye bushingiye ku Mana."),
            dict(icon="coin", name_en="Finance", name_rw="Imari",
                 description_en="Stewardship, not an idol.",
                 description_rw="Ubugenzuzi, atari igishushanyo."),
            dict(icon="shield", name_en="Security", name_rw="Umutekano",
                 description_en="Guarding peace, protecting the vulnerable.",
                 description_rw="Kurinda amahoro, no kurengera abadafite ubushobozi."),
            dict(icon="wave", name_en="Communication & Media", name_rw="Itangazamakuru",
                 description_en="Carrying good news to where people already are.",
                 description_rw="Gutwara ubutumwa bwiza aho abantu basanzwe bari."),
        ]
        for i, data in enumerate(mountains):
            SevenMountain.objects.update_or_create(name_en=data["name_en"], defaults=dict(order=i, **{k: v for k, v in data.items() if k != "name_en"}))
        self.stdout.write("Seven mountains ready.")

    # ------------------------------------------------------------- beliefs
    def seed_beliefs(self):
        beliefs = [
            dict(title_en="Scripture", title_rw="Ibyanditswe Byera",
                 description_en="The Bible is God's inspired word and our final authority for faith and life.",
                 description_rw="Bibiliya n'ijambo ry'Imana ryahumetswe kandi ni ryo shingiro ry'ukwizera n'ubuzima bwacu."),
            dict(title_en="One God, three persons", title_rw="Imana Imwe, Abantu Batatu",
                 description_en="We worship one God who exists eternally as Father, Son, and Holy Spirit.",
                 description_rw="Dusenga Imana imwe ibaho iteka nka Data, Umwana, n'Umwuka Wera."),
            dict(title_en="Salvation", title_rw="Agakiza",
                 description_en="We are saved by grace, through faith in Jesus Christ alone.",
                 description_rw="Dukizwa n'ubuntu, binyuze mu kwizera Yesu Kristo gusa."),
            dict(title_en="The altar", title_rw="Igicaniro",
                 description_en="A daily, personal life of prayer — not only gathering in a crowd — is where this movement begins and stays alive.",
                 description_rw="Ubuzima bw'isengesho bwa buri munsi, bwite — atari gusa guteranira mu bwinshi — niho uyu muvuko utangirira kandi ugakomeza kubaho."),
            dict(title_en="The Holy Spirit", title_rw="Umwuka Wera",
                 description_en="The Holy Spirit is present and active today, empowering holy living and mission.",
                 description_rw="Umwuka Wera arahari kandi arakora muri iki gihe, ugatanga imbaraga zo kubaho no gukora umurimo."),
            dict(title_en="Sent, not hidden", title_rw="Twoherejwe, Ntitwihishe",
                 description_en="The Church is sent into every sphere of society — not withdrawn from it.",
                 description_rw="Itorero ryoherejwe mu bice byose by'imibereho — ntabwo ryikuye muri byo."),
        ]
        for i, data in enumerate(beliefs):
            BeliefPoint.objects.update_or_create(title_en=data["title_en"], defaults=dict(order=i, **{k: v for k, v in data.items() if k != "title_en"}))
        self.stdout.write("Beliefs ready.")

    # ------------------------------------------------------------- timeline
    def seed_timeline(self):
        entries = [
            dict(
                year="2020", order=0,
                body_en=(
                    "A calling arrived that year, insisting on one thing: become a builder of hearts. "
                    "It didn't come as a plan or a program — it came as a fire that made staying "
                    "comfortable impossible. The journey out of that fire was a journey toward "
                    "becoming a person shaped by God first, before being useful to anyone else."
                ),
                body_rw=(
                    "Urugendo yakuyemo intego zo kugira imbaraga zumutima (1. Kuba umuntu w'Imana "
                    "otherwise you can be lost)."
                ),
            ),
            dict(
                year="2021", order=1,
                body_en=(
                    "Around eight in the evening, a promise came: a gift was coming. Two days a week "
                    "were set apart to be spent with God alone in the secret place — not in the crowd "
                    "— on Wednesdays and Sundays. The first of those days carried a single instruction: "
                    "Youth Time Revival. A year of learning to listen, learning fellowship, and an altar "
                    "of prayer was born every Friday, held up by three pillars — prayer, faith, and the "
                    "Holy Spirit. The second time those words came, they came as a confrontation: too "
                    "many young people had been shown a counterfeit version of faith, dressed as "
                    "religion, and told that was the ceiling. The answer was revival — not an event, "
                    "but a reformation of spirit, soul, and body. And with it came a sending: to seven "
                    "mountains — politics, entertainment, education, health, finance, security, and "
                    "communication & media — carrying not a slogan, but a changed life."
                ),
                body_rw=(
                    "Around 8pm, he heard God telling him, he will receive a gift. Imana imuha iminsi "
                    "ibiri mu cyumweru yo kubana n'Imana muri temple alone not in masses (Wednesday and "
                    "Sunday). Ubuzima bw'ikinyoma bwa system ya ma dini, narabubonye ndabumenya "
                    "ndabuhishurirwa, byazanywe no kubana n'Imana no gutindana n'Imana mbona ibibirimo. "
                    "Igisubizo ni revival; ububyutse. Revival ni reformation y'Umwuka, ubugingo "
                    "n'umubiri. Nitutemera guterwa tuzahusha. Nzakomeza nkurikirane icy'Umwuka … "
                    "kugarura ishusho y'Imana mu bantu."
                ),
            ),
        ]
        for data in entries:
            CallTimelineEntry.objects.update_or_create(year=data["year"], defaults=data)
        self.stdout.write("Call timeline ready.")

    # ------------------------------------------------------------------ faq
    def seed_faqs(self):
        faqs = [
            dict(question_en="What is Youth Time Revival?", question_rw="Youth Time Revival ni iki?",
                 answer_en="A youth-led movement built around a personal, daily life of prayer — not a single event — that trains young people through teaching, mentorship, and community, and sends them into every part of society.",
                 answer_rw="Ni umuvuko w'urubyiruko ushingiye ku isengesho rya buri munsi, ryihariye — atari igikorwa kimwe gusa — utoza urubyiruko binyuze mu nyigisho, ubuyobozi hafi, n'ubusabane, ukanabohereza mu bice byose by'imibereho.",
                 is_highlighted=True),
            dict(question_en="Do I need to belong to a church to join YTR?", question_rw="Ese ngomba kuba mu itorero kugira ngo njye muri YTR?",
                 answer_en="No. YTR is a movement, not a denomination — young people from any church background are welcome.",
                 answer_rw="Oya. YTR ni umuvuko, ntabwo ari idini — urubyiruko ruva mu matorero atandukanye rwakirwa neza."),
            dict(question_en="What happens at a fellowship gathering?", question_rw="Ni iki kiba mu iteraniro ry'ubusabane?",
                 answer_en="Worship, teaching, open prayer, and time to be known — not just attend.",
                 answer_rw="Iramire, inyigisho, isengesho rifunguye, n'igihe cyo kumenyekana — ntabwo ari uguhagera gusa."),
            dict(question_en="Is YTR only in one city?", question_rw="Ese YTR iri mu mujyi umwe gusa?",
                 answer_en="YTR started locally, but the podcast, articles, and videos are built to reach anyone, anywhere.",
                 answer_rw="YTR yatangiriye ahantu hamwe, ariko podcast, ibyanditswe, na videwo byubatswe kugira ngo bigere ku muntu wese, ahantu hose."),
            dict(question_en="Can I read the articles only in Kinyarwanda?", question_rw="Ese nshobora gusoma ibyanditswe mu Kinyarwanda gusa?",
                 answer_en="Yes — use the EN / KN switch at the top of the page; every article is written in both languages.",
                 answer_rw="Yego — koresha ibuto EN / KN hejuru y'urupapuro; buri gyanditswe ryanditswe mu ndimi zombi."),
            dict(question_en="How do I get involved or serve?", question_rw="Nabigenza nte kugira ngo mfashe cyangwa nkore umurimo?",
                 answer_en="Come to a gathering and speak with the team — most serving starts with showing up consistently.",
                 answer_rw="Za mu iteraniro uganire n'itsinda — imirimo myinshi itangira n'ugaragara buri gihe."),
            dict(question_en="Can I submit a testimony?", question_rw="Ese nashobora kohereza ubuhamya bwanjye?",
                 answer_en="Yes — send it through the contact form and our team will follow up.",
                 answer_rw="Yego — bwohereze binyuze mu ifishi yo kutwandikira, itsinda ryacu rikurikirane."),
            dict(question_en="How can I support YTR financially?", question_rw="Nabasha nte gutera inkunga YTR mu by'imari?",
                 answer_en="Reach out through the contact section for current giving details.",
                 answer_rw="Twandikire binyuze mu gice cyo kuvugana natwe kugira ngo tugusobanurire uburyo."),
            dict(question_en="Where can I listen to Kanguka?", question_rw="Nabasha he kumva Kanguka?",
                 answer_en="The Podcasts section lists every episode; streaming links are being added as they go live.",
                 answer_rw="Igice cya Podcast kirimo ibiganiro byose; imiyoboro yo kumva izongerwaho uko igenda itangira gukora."),
        ]
        for i, data in enumerate(faqs):
            FAQ.objects.update_or_create(question_en=data["question_en"], defaults=dict(order=i, **{k: v for k, v in data.items() if k != "question_en"}))
        self.stdout.write("FAQs ready.")
