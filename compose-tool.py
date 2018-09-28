import os, platform, subprocess, sys, shutil
import hashlib
import distro
from azure.storage.blob import BlockBlobService, PublicAccess


class ImageIso:
    def __init__(self, ks, proj=None, volid=None, filename=None, fedoraver=None, bootname=None):
        self.ks = self.flatten_ks(ks)
        self.proj = proj
        self.volid = volid
        self.filename = filename
        self.fedoraver = fedoraver
        self.bootname = bootname

    def flatten_ks(self, ks):
        run_ksflatten = f'ksflatten --config {ks} -o flat-{ks} --version F{self.fedoraver}'
        ret = subprocess.run(run_ksflatten, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'Error: {ret.stderr}')
            sys.exit(ret.returncode)
        
        return f'flat-{ks}'


class ComposeEnv:
    def __init__(self, ks, fedoraver=None, march=None, chrootdir=None):
        self.ks = ks
        if fedoraver:
            self.fedoraver = fedoraver
        else:
            self.fedoraver = distro.version()
        if march:
            self.march = march
        else:
            self.march = platform.machine()
        if chrootdir:
            self.chrootdir = chrootdir
        else:
            self.chrootdir = f'/var/lib/mock/fedora-{self.fedoraver}-{self.march}/root'
        self.resultdir = f'{self.chrootdir}/var/lmc'
        self.mock = f'mock -r fedora-{self.fedoraver}-{self.march}'


    def setup_builder(self):
        print('Setup builder environment...')
        
        run_init_chroot = f'{self.mock} --root={self.chrootdir} --init'
        ret = subprocess.run(run_init_chroot, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)

        builder_tools = (
                'lorax-lmc-novirt '
                'vim-minimal '
                'pykickstart '
                'git'
        )

        run_install_deps = f'{self.mock} --root={self.chrootdir} --install {builder_tools}'
        ret = subprocess.run(run_install_deps, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)

    
    def compose_iso(self, iso, resultdir=None):
        print('Composing ISO...')

        if not isinstance(iso, ImageIso):
            print('ERROR: need ImageIso object, not {type(iso)}')
            sys.exit(-1)

        if iso.fedoraver != self.fedoraver:
            print(f'ERROR: Fedora version is not matching in ImageIso and ComposeEnv')
            print(f'       ImageIso: Fedora {iso.fedoraver}')
            print(f'       ComposeEnv: Fedora {self.fedoraver}')
            sys.exit(-2)
        
        if os.path.exists(self.chrootdir) != os.path.isdir(self.chrootdir):
            print('ERROR: there is no chroot directory')
            sys.exit(-3)

        shutil.move(iso.ks, self.chrootdir)

        livemedia_creator = (
            f'livemedia-creator --ks {iso.ks} --no-virt --resultdir /var/lmc --project {iso.proj}'
            f' --make-iso --volid {iso.volid} --iso-only --iso-name {iso.filename} --releasever {iso.fedoraver}'
            f' --title {iso.bootname} --macboot'
        )

        run_compose_iso = f'{self.mock} --root={self.chrootdir} --shell --old-chroot "{livemedia_creator}"'
        ret = subprocess.run(run_compose_iso, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)

        if resultdir:
            iso_save_dest = resultdir
        else:
            iso_save_dest = os.getcwd()
        
        if os.path.exists(iso_save_dest) and os.path.isdir(iso_save_dest):
            shutil.move(self.resultdir + 'iso.filename', iso_save_dest)
        else:
            print(f'ERROR: {iso_save_dest} should be a directory and exists')
        
        print(f'ISO has been composed.\nResult: {iso_save_dest}/{iso.filename}')


    def clean(self):
        print('Clean builder environment...')
        
        run_init_chroot = f'{self.mock} --root={self.chrootdir} --clean'
        ret = subprocess.run(run_init_chroot, capture_output=True, text=True, shell=True, encoding='utf-8')
        if ret.returncode != 0:
            print(f'ERROR: {ret.stderr}')
            sys.exit(ret.returncode)


class AzureBlobService(BlockBlobService):
    def progress_cb(self, current, total):
        progress = 100 * (float(current)/float(total))
        print(f'Uploading... ({progress:.{2}f} %)', end='\r')


    def upload(self, container, filepath):
        self.create_blob_from_path(container, filepath.rsplit('/')[-1], filepath, progress_callback=self.progress_cb)


def find_main_ks_cwd():
    files = [f for f in os.listdir() if os.path.isfile(f)]
    return 'main.ks' if 'main.ks' in files else None


def main():
    print(find_main_ks_cwd())


if __name__ == '__main__':
    main()
