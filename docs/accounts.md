# YTR Accounts and Phase B

## Overview

YTR keeps Django's built-in `User` model and extends the existing one-to-one `Profile` model.

This Phase B release adds:

- profile name, phone, and language preferences
- privacy consent tracking and policy version
- email verification before activation
- password reset support using Django's built-in token flow
- an upgraded member dashboard titled My YTR

## Profile fields

The profile model now includes:

- `full_name`
- `phone_number`
- `preferred_language` (`en` or `rw`)
- `privacy_accepted_at`
- `privacy_policy_version`

These fields are nullable/blank compatible for legacy users and are progressively populated during registration.

## Registration flow

The public signup form collects:

- username
- full name
- email
- optional phone
- language
- password
- privacy consent

The account is created as inactive until the email verification step succeeds.

## Verification and login

After signup, the app sends a verification email with a signed token. The user clicks a link under `/accounts/verify-email/.../` and the account is activated.

This keeps the project aligned with the moderated member flow while still delivering a daily-discipleship UX without a custom user model.

## Password reset

Django's built-in password reset routes are enabled under the accounts app, so users can request a reset link from the login screen.

## My YTR dashboard

The member dashboard now presents:

- greeting using the profile's display name
- today’s devotion or a guided empty state
- next gathering
- resource discovery cards for Read / Listen / Watch
- saved resources and RSVP summary
- testimony and prayer request entry points

## Security notes

- the registration form contains a honeypot field to reject bot submissions
- only safe same-host redirect targets are used for member actions
- authenticated member routes remain restricted to the correct role
