import hashlib
import tempfile
import unittest

from ai_nurse_scr import utils

try:
    from ai_nurse_scr.paperqa2 import utils as p2_utils
except Exception:  # just in case
    p2_utils = None


class TestUtils(unittest.TestCase):
    def test_sha256_file_common(self):
        with tempfile.NamedTemporaryFile('wb', delete=False) as tf:
            tf.write(b"hello")
            tf.flush()
            expected = hashlib.sha256(b"hello").hexdigest()
            self.assertEqual(utils.sha256_file(tf.name), expected)
            if p2_utils is not None:
                self.assertEqual(p2_utils.sha256_file(tf.name), expected)
                self.assertIs(p2_utils.sha256_file, utils.sha256_file)


if __name__ == '__main__':
    unittest.main()
