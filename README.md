# td-api-authenticator
A selenium based authenticator for the TD api using a real brokerage account.  Will handle handle all Oauth logic and dump to td_credentials.json. Make sure selenium is properly configured before use.

### Windows Setup
> Make sure "Selenium", "td_auth" and "chromedriver.exe" in driectory
- import "td_auth"
- run "initialize()" function with credentials

```
import td_auth

td_auth.initialize(
        client_id    = '********************************', # API Key
        redirect_uri = 'http://localhost',                 # Example
        username     = "******",                           # Brokerage Account Username
        password     = "******"                            # Brokerage Account Password
    )
```

### Mac Setup
Comming Soon!
