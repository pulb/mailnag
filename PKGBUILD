# Maintainer: Patrick Ulbrich <zulu99 at gmx . net>
# Contributor: rasmus <rasmus . pank at gmail . com>

pkgname=mailnag
pkgver=1.0.0
pkgrel=2
pkgdesc="An extendable mail notification daemon"
arch=('any')
url="https://github.com/pulb/mailnag"
license=('GPL')
depends=('python2' 'python2-gobject' 'python2-httplib2'
        'libgnome-keyring' 'gnome-keyring' 'python2-xdg'
        'python2-dbus' 'libnotify' 'gst-plugins-base'
        'gtk3' 'gdk-pixbuf2')
optdepends=('mailnag-gnome-shell: for a tighter GNOME 3 integration')
makedepends=('gettext')
source=('https://github.com/pulb/mailnag/archive/v1.0.0.tar.gz')
md5sums=('f3c0df790a2f5e6b615ef804ee0e5a91')
install='mailnag.install'

package() {
  cd "${srcdir}/${pkgname}-${pkgver}"
  python2 setup.py install --root=${pkgdir}
  install -D -m644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
