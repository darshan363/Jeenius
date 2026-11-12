"""Regression tests for the ordered cloud-provider fallback."""
import unittest
from unittest.mock import patch
import server

class AIFallbackOrderTests(unittest.TestCase):
    def test_order_is_gemini_keys_groq_then_openrouter(self):
        keys = {
            'GEMINI_API_KEY_1': 'g1', 'GEMINI_API_KEY_2': 'g2', 'GEMINI_API_KEY_3': 'g3',
            'GROQ_API_KEY': 'groq', 'OPENROUTER_API_KEY': 'router',
            'OPENROUTER_MODEL': 'google/gemma-4-31b-it:free',
        }
        calls = []
        def fail_gemini(model, key, *args):
            calls.append(('gemini', key)); raise RuntimeError('expected test failure')
        def fail_groq(key, *args):
            calls.append(('groq', key)); raise RuntimeError('expected test failure')
        def pass_router(key, *args):
            calls.append(('openrouter', key)); return 'fallback reply'
        with patch.object(server, 'env', return_value=keys), \
             patch.object(server, 'callGemini', side_effect=fail_gemini), \
             patch.object(server, 'callGroq', side_effect=fail_groq), \
             patch.object(server, 'callOpenRouter', side_effect=pass_router), \
             patch.object(server, 'labs', return_value=[]), \
             patch.object(server, 'buildBehaviorPrompt', return_value='lab prompt'):
            result = server.genie({'message': 'Explain force', 'history': []})
        self.assertEqual([item for kind, item in calls], ['g1', 'g2', 'g3', 'groq', 'router'])
        self.assertEqual(result['reply'], 'fallback reply')
        self.assertEqual(result['model'], 'google/gemma-4-31b-it:free')

    def test_accepts_gemini_api_key_aliases_without_underscores(self):
        keys = {
            'GEMINI_API_KEY1': 'g1', 'GEMINI_API_KEY2': 'g2', 'GEMINI_API_KEY3': 'g3',
        }
        calls = []
        def fail_gemini(model, key, *args):
            calls.append(key)
            raise RuntimeError('expected test failure')
        with patch.object(server, 'env', return_value=keys), \
             patch.object(server, 'callGemini', side_effect=fail_gemini), \
             patch.object(server, 'callGroq', side_effect=RuntimeError('not configured')), \
             patch.object(server, 'callOpenRouter', side_effect=RuntimeError('not configured')), \
             patch.object(server, 'labs', return_value=[]), \
             patch.object(server, 'buildBehaviorPrompt', return_value='lab prompt'):
            server.genie({'message': 'Explain force', 'history': []})
        self.assertEqual(calls, ['g1', 'g2', 'g3'])

    def test_catalog_includes_unlisted_animation_folder(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'animations'/'99-new-test').mkdir(parents=True)
            (root/'animations'/'99-new-test'/'index.html').write_text('<h1>Test</h1>')
            (root/'animations'/'_shared').mkdir(parents=True)
            (root/'animations'/'_shared'/'index.html').write_text('shared')
            (root/'labs.json').write_text('[{"id":"01-existing","title":"Existing","available":true}]')
            old_pub = server.PUB
            try:
                server.PUB = root
                result = server.labs()
            finally:
                server.PUB = old_pub
        self.assertEqual([lab['id'] for lab in result], ['01-existing', '99-new-test'])
        self.assertTrue(result[0]['available'] is False)
        self.assertTrue(result[1]['available'] is True)

if __name__ == '__main__':
    unittest.main()
