try:
    from http import HTTPStatus
    HTTP_STATUS_FOUND = HTTPStatus.FOUND
except ImportError:
    from httplib import FOUND as HTTP_STATUS_FOUND

import pytest
import requests
import requests_mock


def test_simple(requests_mock):
    requests_mock.get('https://httpbin.org/get', text='data')
    assert 'data' == requests.get('https://httpbin.org/get').text


def test_redirect_and_nesting():
    url_inner = "inner-mock://example.test/"
    url_middle = "middle-mock://example.test/"
    url_outer = "outer-mock://example.test/"
    url_base = "https://www.example.com/"

    text_middle = 'middle' + url_middle
    text_outer = 'outer' + url_outer
    text_base = 'outer' + url_base

    with requests_mock.Mocker() as outer_mock:
        outer_mock.get(url_base, text=text_base)
        outer_mock.get(url_outer, text=text_outer)

        with requests_mock.Mocker(real_http=True) as middle_mock:
            middle_mock.get(url_middle, text=text_middle)

            with requests_mock.Mocker() as inner_mock:
                inner_mock.post(url_inner,
                                status_code=HTTP_STATUS_FOUND,
                                headers={'location': url_base})
                inner_mock.get(url_base, real_http=True)

                assert text_base == requests.post(url_inner).text  # nosec

                with pytest.raises(requests_mock.NoMockAddress):
                    requests.get(url_middle)

                with pytest.raises(requests_mock.NoMockAddress):
                    requests.get(url_outer)

            # back to middle mock
            with pytest.raises(requests_mock.NoMockAddress):
                requests.post(url_inner)

            assert text_middle == requests.get(url_middle).text  # nosec
            assert text_outer == requests.get(url_outer).text  # nosec

        # back to outter mock
        with pytest.raises(requests_mock.NoMockAddress):
            requests.post(url_inner)

        with pytest.raises(requests_mock.NoMockAddress):
            requests.get(url_middle)

        assert text_outer == requests.get(url_outer).text  # nosec


def test_mixed_mocks():
    url = 'mock://example.test/'
    with requests_mock.Mocker() as global_mock:
        global_mock.get(url, text='global')
        session = requests.Session()
        text = session.get(url).text
        assert text == 'global'  # nosec
        with requests_mock.Mocker(session=session) as session_mock:
            session_mock.get(url, real_http=True)
            text = session.get(url).text
            assert text == 'global'  # nosec


def test_threaded_sessions():
    return
    """
    When using requests_futures.FuturesSession() with a ThreadPoolExecutor
    there is a race condition where one threaded request removes the
    monkeypatched get_adapter() method from the Session before another threaded
    request is finished using it.
    """
    import time

    from requests_futures.sessions import FuturesSession
    from requests_mock.adapter import Adapter

    url1 = 'http://www.example.com/requests-mock-fake-url1'
    url2 = 'http://www.example.com/requests-mock-fake-url2'

    fetching = set()

    class BlockingAdapter(Adapter):
        def send(self, request, **kwargs):
            assert request.url not in fetching

            # neither request is allowed to complete until both have been started
            fetching.add(request.url)
            start_time = time.time()
            while len(fetching) < 2:
                time.sleep(0.01)

                elapsed = time.time() - start_time
                assert elapsed < 5, "2nd fetch has not started - presumed deadlock condition"

            result = super(BlockingAdapter, self).send(request, **kwargs)

            return result

    with requests_mock.Mocker() as m:
        # respond with 204 so we know its us
        m.get(url1, status_code=204)
        m.get(url2, status_code=204)

        # NOTE(phodge): just firing off two .get() requests right after each
        # other was a pretty reliable way to reproduce the race condition on my
        # intel Macbook Pro but YMMV. Guaranteeing the race condition to
        # reappear might require replacing the Session.send() with a wrapper
        # that delays kicking off the request for url1 until the request for
        # url2 has restored the original session.get_adapter(), but replacing
        # Session.send() could be difficult because the requests_mock.Mocker()
        # context manager has *already* monkeypatched this method.
        session = FuturesSession()
        future1 = session.get(url1)

        # Without the threading lock, you can add a short sleep() here to avoid
        # the race condition (future1 fully completes before future2 begins)
        #time.sleep(1)

        # BUT because we are using the BlockingAdapter(), that should *force*
        # us to encounter the race condition anyway - it will block the first
        # future until the 2nd one has a chance to catch up

        future2 = session.get(url2)

        # verify both requests were handled by the mock dispatcher
        assert future1.result().status_code == 204
        assert future2.result().status_code == 204
    #assert result3.status_code == 204
    #assert result4.status_code == 204
    #assert result5.status_code == 204
    raise Exception("TODO: assert the response codes")  # noqa
    token_response_future = session.post(
        url=DROPBOX_OAUTH2_TOKEN_URL,
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data=payload)
    import pprint, sys
    sys.stderr.write('DROPBOX_OAUTH2_TOKEN_URL(2) = {}\n'.format(
        pprint.pformat(DROPBOX_OAUTH2_TOKEN_URL)))  # noqa TODO

    try:
        sys.stderr.write('DROPBOX_JWK_ENDPOINT(2) = {}\n'.format(
            pprint.pformat(DROPBOX_JWK_ENDPOINT)))  # noqa TODO
        public_key_response = session.get(url=DROPBOX_JWK_ENDPOINT).result()
        requests.create_exception(public_key_response)
        import pprint, sys
        sys.stderr.write('public_key_response = {}\n'.format(
            pprint.pformat(public_key_response)))  # noqa TODO
    except (requests.HTTPError, requests.ConnectTimeout) as err:
        logger.error('Failure to fetch Dropbox JWK document (HTTP/%i): %s' %
                     (err.response.status_code, common.helpers.ensure_unicode(err.response.text)))
        session.close()
        return None, None, AUTH_ERRORS.ERROR_OCCURRED

    try:
        token_response = token_response_future.result()
        requests.create_exception(token_response)
    except (requests.HTTPError, requests.ConnectTimeout) as err:
        import pprint, sys
        sys.stderr.write('err = {}\n'.format(pprint.pformat(err)))  # noqa TODO
        logger.error('Failure to redeem Dropbox authorization token (HTTP/%i): %s' %
                     (err.response.status_code, common.helpers.ensure_unicode(err.response.text)))
        session.close()
        return None, None, AUTH_ERRORS.INVALID_CREDENTIALS

    dropbox_public_jwk = None
    raise Exception("TODO: yeah nah")  # noqa


class TestClass(object):

    def configure(self, requests_mock):
        requests_mock.get('https://httpbin.org/get', text='data')

    def test_one(self, requests_mock):
        self.configure(requests_mock)
        assert 'data' == requests.get('https://httpbin.org/get').text
