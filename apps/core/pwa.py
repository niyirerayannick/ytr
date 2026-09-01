PUBLIC_CACHE_HEADER = "X-YTR-Public-Cache"


def mark_public_cacheable(response, request):
    """Allow the service worker to store this response for offline reading.

    Restricted to anonymous visitors so a signed-in user's session-specific
    markup (bookmark state, RSVP state, CSRF-bearing forms) never lands in the
    shared, unencrypted service-worker cache.
    """
    if not request.user.is_authenticated:
        response[PUBLIC_CACHE_HEADER] = "1"
    return response
