# Useful

## Rules for frontend

### Social Auth

**1.** **Get social login url:** `GET /auth/social/{social_type}/url`

Redirect to social login or `/personal_area`

**2.** **Redirects**

* `/connect/error?error={error}&error_description={error_description}`

    **error** - error status code
    **error_description** - error description

* `/connect/code=<code>` - successful user authorization.

    Then need to send a request to `POST /auth/social/token` with recevied code, then will be returned pair of aceess and refresh tokens.

* `/connect/mail?code={code}` - successful user authorization, but user 
    has no email.

    You need to get an email from the user and send a request to `POST /auth/social/send_confirmation_email`. When the user confirms his email account will be activated.



### Social Bind

**1.** **Bind:** `GET /auth/social/{social_type}/bind`

The url will be returned to which you need to redirect the user.

If the account is already linked to another user, then a redirect to: `/connect/error?error=<error_text>`.

If successful, a redirect to `/personal_area`.

**2.** **Unbind:** `GET /auth/social/{social_type}/unbind`

Will remove social auth for specific user.

**3.** Getting a user's **list of linked socials:** `GET /auth/social`

Retrieve a user's list of bound socials.
