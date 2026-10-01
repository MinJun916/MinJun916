import unittest
import xml.etree.ElementTree as ET
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location('renderer', Path(__file__).with_name('render-language-metrics.py'))
renderer = module_from_spec(spec)
spec.loader.exec_module(renderer)
NS = {'s': 'http://www.w3.org/2000/svg'}


def source(count=8, summary='estimation from 22.5mb of code in 12664 edited files across 2496 commits'):
    rows = ''.join(f'<div class="field language details"><div><svg><path fill="#3178c6"/></svg>Language {index}</div><small><div>{index + 100}k lines</div><div>{index + 1}.25%</div></small></div>' for index in range(count))
    return f'<svg><div><small>{summary}</small>{rows}</div></svg>'


class LanguageCardTest(unittest.TestCase):
    def test_preserves_statistics_and_sorts_ranking(self):
        root = ET.fromstring(renderer.render(source()))
        text = [item.text for item in root.findall('.//s:text', NS)]
        for index in range(8):
            self.assertIn(f'Language {index}', text)
            self.assertIn(f'{index + 100}k lines', text)
            self.assertIn(f'{index + 1}.25%', text)
        names = [value for value in text if value.startswith('Language ')]
        self.assertEqual(names, [f'Language {i}' for i in reversed(range(8))])
        self.assertIsNone(root.find('.//s:foreignObject', NS))

    def test_all_rows_and_wrapped_summary_fit_canvas(self):
        for count in [1, 8, 15]:
            root = ET.fromstring(renderer.render(source(count, 'estimation from ' + 'a long summary ' * 20)))
            height = float(root.attrib['height'])
            for node in root.findall('.//s:text', NS):
                self.assertLess(float(node.attrib['y']) + 5, height)
            for node in root.findall('.//s:rect', NS)[1:]:
                self.assertLess(float(node.attrib['y']) + float(node.attrib['height']), height)
                self.assertLessEqual(float(node.attrib['x']) + float(node.attrib['width']), 480)

    def test_missing_or_invalid_data_fails(self):
        for invalid in ['<svg/>', source().replace('1.25%', 'nan%'), source().replace('1.25%', '101%')]:
            with self.assertRaises(ValueError):
                renderer.render(invalid)


if __name__ == '__main__':
    unittest.main()
