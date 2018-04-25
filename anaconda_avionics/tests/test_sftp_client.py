import unittest
from anaconda_avionics.utilities import SFTPClient

class SFTPClientTest(unittest.TestCase):
    """SFTP download test."""

    def test_sftp_download(self):
        sftp = SFTPClient('pi', 'raspberry', 'cameratrap.local')

        sftp.downloadAndDeleteAllFiles()

        sftp.close()

if __name__ == '__main__':
    unittest.main()