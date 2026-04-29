from __future__ import annotations

import unittest

import pandas as pd

from scripts.v03_gcn.config import GcnConfig
from scripts.v03_gcn.gdelt import aggregate_gdelt_pressure


class GdeltTests(unittest.TestCase):
    def test_aggregate_gdelt_pressure_uses_bidirectional_country_pairs(self) -> None:
        events = pd.DataFrame(
            [
                {
                    "SQLDATE": 20190102,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -5.0,
                    "NumMentions": 2,
                    "AvgTone": -1.0,
                    "SOURCEURL": "https://example.test/semiconductor-export-control",
                },
                {
                    "SQLDATE": 20190304,
                    "Actor1CountryCode": "CHN",
                    "Actor2CountryCode": "USA",
                    "GoldsteinScale": -3.0,
                    "NumMentions": 4,
                    "AvgTone": -2.0,
                    "SOURCEURL": "https://example.test/chip-sanction",
                },
                {
                    "SQLDATE": 20190506,
                    "Actor1CountryCode": "JPN",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": 2.0,
                    "NumMentions": 1,
                    "AvgTone": 1.0,
                    "SOURCEURL": "https://example.test/chip-supply-chain",
                },
            ]
        )
        crosswalk = pd.DataFrame(
            [
                {"exporter_code": 842, "exporter_iso3": "USA", "gdelt_country_code": "USA"},
                {"exporter_code": 392, "exporter_iso3": "JPN", "gdelt_country_code": "JPN"},
            ]
        )

        result = aggregate_gdelt_pressure(events, crosswalk, years=(2019,), config=GcnConfig())
        by_code = result.set_index("exporter_code")

        self.assertEqual(by_code.loc[842, "gdelt_event_count"], 2)
        self.assertEqual(by_code.loc[842, "gdelt_negative_goldstein_sum"], 22.0)
        self.assertEqual(by_code.loc[842, "gdelt_mentions"], 6)
        self.assertEqual(by_code.loc[392, "gdelt_event_count"], 1)
        self.assertEqual(by_code.loc[392, "gdelt_negative_goldstein_sum"], 0.0)
        self.assertEqual(by_code.loc[842, "gdelt_filter_mode"], "pre_filtered")

    def test_keyword_filter_keeps_only_matching_text_events(self) -> None:
        events = pd.DataFrame(
            [
                {
                    "SQLDATE": 20190102,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -5.0,
                    "NumMentions": 2,
                    "AvgTone": -1.0,
                    "SOURCEURL": "https://example.test/semiconductor",
                },
                {
                    "SQLDATE": 20190202,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -8.0,
                    "NumMentions": 10,
                    "AvgTone": -9.0,
                    "SOURCEURL": "https://example.test/sports",
                },
            ]
        )
        crosswalk = pd.DataFrame([{"exporter_code": 842, "exporter_iso3": "USA", "gdelt_country_code": "USA"}])
        config = GcnConfig(gdelt_apply_keyword_filter=True)

        result = aggregate_gdelt_pressure(events, crosswalk, years=(2019,), config=config)
        row = result.iloc[0]

        self.assertEqual(row["gdelt_event_count"], 1)
        self.assertEqual(row["gdelt_negative_goldstein_sum"], 10.0)
        self.assertEqual(row["gdelt_filter_mode"], "keyword_filtered")

    def test_missing_country_years_are_zero_filled_and_scaled_from_training_years(self) -> None:
        events = pd.DataFrame(
            [
                {
                    "SQLDATE": 20080102,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -1.0,
                    "NumMentions": 1,
                    "AvgTone": -1.0,
                    "SOURCEURL": "https://example.test/chip",
                },
                {
                    "SQLDATE": 20190102,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -5.0,
                    "NumMentions": 5,
                    "AvgTone": -2.0,
                    "SOURCEURL": "https://example.test/chip",
                },
                {
                    "SQLDATE": 20220102,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -50.0,
                    "NumMentions": 50,
                    "AvgTone": -9.0,
                    "SOURCEURL": "https://example.test/chip",
                },
            ]
        )
        crosswalk = pd.DataFrame(
            [
                {"exporter_code": 842, "exporter_iso3": "USA", "gdelt_country_code": "USA"},
                {"exporter_code": 392, "exporter_iso3": "JPN", "gdelt_country_code": "JPN"},
            ]
        )

        result = aggregate_gdelt_pressure(events, crosswalk, years=(2008, 2019, 2020, 2022), config=GcnConfig())
        missing_jpn = result.loc[(result["exporter_code"] == 392) & (result["year"] == 2020)].iloc[0]
        clipped_usa = result.loc[(result["exporter_code"] == 842) & (result["year"] == 2022)].iloc[0]

        self.assertEqual(missing_jpn["gdelt_event_count"], 0)
        self.assertEqual(missing_jpn["gdelt_pressure_score"], 0.0)
        self.assertLessEqual(clipped_usa["gdelt_pressure_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
