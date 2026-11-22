import unittest

try:
    from joycon2_assistant.protocol import identify_advertisement
except ImportError:
    identify_advertisement = None


class AdvertisementTests(unittest.TestCase):
    def test_side_and_fresh_pairing_are_decoded(self):
        self.assertIsNotNone(identify_advertisement, 'Advertisement decoding is not implemented')
        left = bytes.fromhex('0100037e0567200001000000000000000f00000000000000')
        right = bytes.fromhex('0100037e0566200001000000000000000f00000000000000')
        self.assertEqual(identify_advertisement(left), ('left', True))
        self.assertEqual(identify_advertisement(right), ('right', True))

    def test_reconnect_is_distinguished_from_fresh_pairing(self):
        self.assertIsNotNone(identify_advertisement, 'Advertisement decoding is not implemented')
        reconnect = bytes.fromhex('0100037e0567200001001122334455660f00000000000000')
        self.assertEqual(identify_advertisement(reconnect), ('left', False))

    def test_other_devices_and_truncated_data_are_ignored(self):
        self.assertIsNotNone(identify_advertisement, 'Advertisement decoding is not implemented')
        self.assertIsNone(identify_advertisement(b''))
        self.assertIsNone(identify_advertisement(bytes.fromhex('0100037e0569200001000000000000000f')))


if __name__ == '__main__':
    unittest.main()
