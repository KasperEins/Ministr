import unittest
import sys
import os
import pandas as pd

# Add parent directory to path to import data_loader
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_loader import DataLoader

class TestDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.loader = DataLoader()

    def test_economic_indicators(self):
        print("\nTesting Economic Indicators...")
        data = self.loader.load_economic_indicators()
        self.assertIsNotNone(data, "Economic data should not be None")
        
        # Check specific expected keys
        required_keys = ['culture_share_gdp', 'total_financial_resources', 'avg_monthly_wage']
        for key in required_keys:
            self.assertIn(key, data, f"Missing key: {key}")
            
        # Value sanity checks
        self.assertGreater(data['culture_share_gdp'], 0, "GDP share should be positive")
        self.assertGreater(data['avg_monthly_wage'], 20000, "Wage seems abnormally low")
        print("✅ Economic data looks valid.")

    def test_unesco_sites(self):
        print("\nTesting UNESCO Sites...")
        df = self.loader.load_unesco_sites()
        self.assertFalse(df.empty, "UNESCO dataframe should not be empty")
        
        # Check columns
        required_cols = ['name', 'lat', 'lon', 'visitors_2024']
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing column: {col}")
            
        # Check row count (we expect around 19 from the fallback file)
        self.assertGreaterEqual(len(df), 15, "Expected at least 15 UNESCO sites")
        print(f"✅ Loaded {len(df)} UNESCO sites.")

    def test_artist_registry(self):
        print("\nTesting Artist Registry...")
        data = self.loader.load_artist_status()
        self.assertIsNotNone(data, "Artist data should not be None")
        
        self.assertIn('registered_count', data)
        self.assertIn('disciplines', data)
        
        # Check count
        self.assertGreater(data['registered_count'], 0, "Registered count should be positive")
        
        # Check disciplines
        disciplines = data['disciplines']
        self.assertTrue(len(disciplines) > 0, "Should have discipline breakdown")
        print(f"✅ Artist Registry: {data['registered_count']} registered.")

if __name__ == '__main__':
    unittest.main()
