import hashlib
import hmac
import requests
from requests_toolbelt import MultipartEncoder


class Bot:

    DEFAULT_API_VERSION = 6.0

    def __init__(self, access_token, **kwargs):
        self.api_version = kwargs.get('api_version',
                                      self.DEFAULT_API_VERSION)
        self.app_secret = kwargs.get('app_secret')
        self.graph_url = 'https://graph.facebook.com/v{0}' \
                         .format(self.api_version)
        self.access_token = access_token

    def generate_appsecret_proof(self):
        hmac_object = hmac.new(bytearray(self.app_secret, 'utf8'),
                               str(self.access_token).encode('utf8'),
                               hashlib.sha256)
        generated_hash = hmac_object.hexdigest()
        return generated_hash

    def validate_hub_signature(self, request_payload, hub_signature_header):
        try:
            hash_method, hub_signature = hub_signature_header.split('=')
        except (BaseException):
            pass
        else:
            digest_module = getattr(hashlib, hash_method)
            hmac_object = hmac.new(str(self.app_secret),
                                   unicode(request_payload), digest_module)
            generated_hash = hmac_object.hexdigest()
            if hub_signature == generated_hash:
                return True
        return False

    @property
    def auth(self):
        if not hasattr(self, '_auth'):
            auth = {
                'access_token': self.access_token
            }
            if self.app_secret is not None:
                auth['appsecret_proof'] = self.generate_appsecret_proof()
            self._auth = auth
        return self._auth

    def _request(self, url, verb='POST', *args, **kwargs):
        if url.startswith('/'):
            url = "%s%s" % (self.graph_url, url)
        method = getattr(requests, verb.lower())
        return method(url, *args, **kwargs)

    def _send_payload(self, recipient_id, payload):
        return self._request(url='/me/messages',
                             params=self.auth,
                             json=dict(recipient={'id': recipient_id},
                                       **payload)).json()

    def _send_message(self, recipient_id, message):
        return self._send_payload(recipient_id, {'message': message})

    def get_user_info(self, user_id, fields=None):
        params = {}
        if fields is not None and isinstance(fields, (list, tuple)):
            params['fields'] = ",".join(fields)

        params.update(self.auth)

        req = self._request('/%s' % user_id,
                            verb='GET',
                            params=params)

        if req.status_code == 200:
            return req.json()
        return None

    def send_text_message(self, recipient_id, message):
        return self._send_message(recipient_id, {'text': message})

    def send_message(self, recipient_id, message):
        return self._send_message(recipient_id, message)

    def send_generic_message(self, recipient_id, elements):
        return self._send_message(recipient_id, {"attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": elements
                    }
                }})

    def send_button_message(self, recipient_id, text, buttons):
        return self._send_message(recipient_id, {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "button",
                                "text": text,
                                "buttons": buttons
                            }
                        }
                    })

    def send_action(self, recipient_id, action):
        return self._send_payload(recipient_id,
                                  {'sender_action': action})

    def _send_url(self, recipient_id, file_type, url):
        """
        Send an attachment by URL.
        """
        return self._send_message(recipient_id,
                                  {'attachment': {
                                        'type': file_type,
                                        'payload': {
                                            'url': url
                                        }
                                    }
                                   })

    # def send_audio_url(self, recipient_id, url):
    #     return self._send_url(recipient_id, 'audio', url)

    # def send_image_url(self, recipient_id, url):
    #     return self._send_url(recipient_id, 'image', url)

    # def send_file_url(self, recipient_id, url):
    #     return self._send_url(recipient_id, 'file', url)

    # def send_video_url(self, recipient_id, url):
    #     return self._send_url(recipient_id, 'file', url)

    def _send_by_path(self, recipient_id, file_type, path):
        """
        Send file contents by path.
        """
        # return self._request( ## what URL .. ##)
        payload = MultipartEncoder({'recipient': {
                    'id': recipient_id
                },
                'message': {
                    'attachment': {
                        'type': file_type,
                        'payload': {}
                    }
                },
                'filedata': (path, open(path, 'rb'))
                })
        header = {'Content-Type': payload.content_type}
        return self._request('',
                             data=payload,
                             headers=header).json()

    # def send_audio(self, recipient_id, path):
    #     return self._send_by_path(recipient_id, 'audio', path)

    # def send_image(self, recipient_id, path):
    #     return self._send_by_path(recipient_id, 'image', path)

    # def send_file(self, recipient_id, path):
    #     return self._send_by_path(recipient_id, 'file', path)

    # def send_video(self, recipient_id, path):
    #     return self._send_by_path(recipient_id, 'video', path)
