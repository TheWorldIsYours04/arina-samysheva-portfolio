#!/usr/bin/env python3
"""Browser regression for project copy and mobile navigation. Never sends real mail.
Install: pip install playwright==1.57.0; playwright install --with-deps chromium webkit
Run: python tests/ui_regression.py [--base-url https://example/portfolio/]
"""
import argparse, functools, json, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'test-results'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url')
    parser.add_argument('--browsers', default='chromium,webkit')
    args = parser.parse_args()
    server = None
    if args.base_url:
        base = args.base_url.rstrip('/') + '/'
    else:
        handler = functools.partial(QuietHandler, directory=str(ROOT / 'site'))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = 'http://127.0.0.1:%s/' % server.server_port
    projects = json.loads((ROOT / 'source/projects.json').read_text())
    intros = json.loads((ROOT / 'source/introductions.json').read_text())
    ARTIFACTS.mkdir(exist_ok=True)
    checks = []
    try:
        with sync_playwright() as pw:
            for engine in args.browsers.split(','):
                browser = getattr(pw, engine).launch()
                for width in (320, 390, 1440):
                    mobile = width <= 680
                    context = browser.new_context(viewport={'width': width, 'height': 844},
                                                  is_mobile=mobile, has_touch=mobile)
                    # An unconditional route blocks every real Formspree request.
                    context.route('https://formspree.io/**', lambda r: r.fulfill(
                        status=200, content_type='application/json', body='{"ok":true}'))
                    for project in projects:
                        page = context.new_page()
                        errors = []
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        slug = project['slug']
                        page.goto(urljoin(base, 'projects/' + slug + '.html'))
                        expect(page.locator('.project-intro h1')).to_be_visible()
                        expect(page.locator('.project-intro h1')).to_have_text(project['title'])
                        expect(page.locator('.project-description')).to_contain_text(intros[slug]['paragraphs'][0])
                        assert page.locator('.project-description p').count() == 1
                        assert page.locator('.slide-link').count() == len(project['slides'])
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                        assert page.locator('.site-nav a').first.evaluate(
                            '(a)=>getComputedStyle(a).color') == 'rgb(2, 42, 85)'
                        if mobile:
                            button = page.locator('.menu-toggle')
                            nav = page.locator('.site-nav')
                            expect(nav).not_to_be_visible()
                            for y in (1600, 0):
                                page.evaluate('(y)=>window.scrollTo(0,y)', y)
                                button.tap()
                                expect(nav).to_be_visible()
                                expect(nav.locator('a')).to_have_text(['Главная', 'Мои работы', 'Контакты'])
                                assert nav.bounding_box()['height'] < 200
                                page.keyboard.press('Escape')
                                expect(nav).not_to_be_visible()
                            assert page.locator('.site-header').bounding_box()['height'] == 64
                            button.tap()
                            nav.get_by_role('link', name='Мои работы', exact=True).tap()
                            page.wait_for_url('**/works.html')
                            assert page.locator('.project-card').count() == 9
                            page.go_back(wait_until='load')
                            expect(page.locator('.site-nav')).not_to_be_visible()
                            page.locator('.menu-toggle').tap()
                            expect(page.locator('.site-nav')).to_be_visible()
                            page.evaluate('window.dispatchEvent(new Event("pageshow"))')
                            expect(page.locator('.site-nav')).not_to_be_visible()
                            if width == 390 and slug == 'bosch':
                                page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
                                page.screenshot(path=str(ARTIFACTS / (engine + '-bosch-mobile.png')))
                                page.locator('.menu-toggle').tap()
                                page.screenshot(path=str(ARTIFACTS / (engine + '-bosch-menu.png')))
                        assert not errors, errors
                        checks.append({'engine': engine, 'width': width, 'page': slug, 'passed': True})
                        page.close()
                    for name in ('index.html', 'works.html', 'contact.html'):
                        page = context.new_page()
                        page.goto(urljoin(base, name))
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                        if name == 'works.html' and mobile:
                            assert abs(page.locator('.project-grid').bounding_box()['width'] - width) < 1
                            assert page.locator('.brand').bounding_box()['x'] < page.locator('.menu-toggle').bounding_box()['x']
                            if width == 390:
                                page.screenshot(path=str(ARTIFACTS / (engine + '-works-mobile.png')))
                        if name == 'index.html':
                            page.locator('[data-contact-email]').click()
                            expect(page.locator('#email-contact-dialog')).to_be_visible()
                            expect(page.locator('[data-email-address]')).to_have_value('arina.samysheva@mail.ru')
                            page.locator('[data-email-close]').click()
                        if name == 'contact.html':
                            assert page.locator('#contact-form').get_attribute('action') == 'https://formspree.io/f/myekpnod'
                            page.locator('#name').fill('Проверка интерфейса')
                            page.locator('#email').fill('qa@example.invalid')
                            page.locator('#message').fill('Тестовый запрос перехватывается внутри теста. Письмо не отправляется.')
                            page.locator('[type=submit]').click()
                            expect(page.locator('#form-status')).to_contain_text('успешно отправлено')
                        checks.append({'engine': engine, 'width': width, 'page': name, 'passed': True})
                        page.close()
                    context.close()
                browser.close()
    finally:
        (ARTIFACTS / 'ui-report.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2))
        if server:
            server.shutdown()
    print('PASS: %s page/viewport/browser checks; no real form submission.' % len(checks))

if __name__ == '__main__':
    main()
