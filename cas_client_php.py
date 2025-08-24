# cas_client_php.py
from urllib.parse import urlencode, urljoin
from cas import CASClientV3

class CASClientV3PHP(CASClientV3):
    # Use our filename endpoint instead of 'p3/serviceValidate'
    url_suffix = 'p3_serviceValidate.php'

    def get_login_url(self):
        params = {'service': self.service_url}
        if self.renew:
            params['renew'] = 'true'
        params.update(self.extra_login_params or {})
        return urljoin(self.server_url, 'login.php') + '?' + urlencode(params)

    # (Optional) if you want a real logout endpoint filename:
    # def get_logout_url(self, redirect_url=None):
    #     if redirect_url:
    #         return urljoin(self.server_url, 'logout.php') + '?' + urlencode({'service': redirect_url})
    #     return urljoin(self.server_url, 'logout.php')
