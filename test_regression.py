import unittest
import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from verification_engine import AddressVerificationEngine, ResolutionReason

class TestAddressResolutionRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the verification engine
        db_path = os.path.join(os.path.dirname(__file__), "backend", "pincodes_in.db")
        cls.engine = AddressVerificationEngine(db_path=db_path)

    def test_kolkata_metro_case_issue_42(self):
        # 1. Kolkata Metro case: Pincode 700091 is North 24 Parganas, but user enters Kolkata
        raw_pred = {
            "house_number": "Flat 394",
            "street": "M G Road",
            "city": "Kolkata",
            "state_area": "West Bengal",
            "postal_code": "700091"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        self.assertEqual(resolved["display_city"], "Kolkata")
        self.assertEqual(resolved["routing_district"], "North 24 Parganas")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.PIN_COMPATIBLE)
        self.assertEqual(verif["confidence"], 0.95)

    def test_hyderabad_metro_case(self):
        # 2. Hyderabad Metro case: Pincode 500032 is K.V.Rangareddy, but user enters Hyderabad
        raw_pred = {
            "house_number": "Plot 14",
            "street": "Kondapur",
            "city": "Hyderabad",
            "state_area": "Telangana",
            "postal_code": "500032"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        self.assertEqual(resolved["display_city"], "Hyderabad")
        self.assertEqual(resolved["routing_district"], "K.V.Rangareddy")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.PIN_COMPATIBLE)
        self.assertEqual(verif["confidence"], 0.95)

    def test_same_state_mismatch(self):
        # 3. Same-state mismatch: Pincode 713301 is Asansol (Paschim Bardhaman), but user enters Kolkata
        raw_pred = {
            "house_number": "Plot 1",
            "street": "Station Road",
            "city": "Kolkata",
            "state_area": "West Bengal",
            "postal_code": "713301"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        # Should be overwritten
        self.assertEqual(resolved["display_city"], "Paschim Bardhaman")
        self.assertEqual(resolved["routing_district"], "Paschim Bardhaman")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.INVALID_CITY)
        self.assertEqual(verif["confidence"], 0.20)

    def test_wrong_state_mismatch(self):
        # 4. Wrong-state mismatch: Pincode 700091 is West Bengal, but user enters Mumbai
        raw_pred = {
            "house_number": "Flat 394",
            "street": "M G Road",
            "city": "Mumbai",
            "state_area": "West Bengal",
            "postal_code": "700091"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        # Should be overwritten
        self.assertEqual(resolved["display_city"], "North 24 Parganas")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.INVALID_CITY)
        self.assertEqual(verif["confidence"], 0.20)

    def test_garbage_input(self):
        # 5. Garbage city input
        raw_pred = {
            "house_number": "Flat 394",
            "street": "M G Road",
            "city": "Banana",
            "state_area": "West Bengal",
            "postal_code": "700091"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        # Should be overwritten
        self.assertEqual(resolved["display_city"], "North 24 Parganas")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.INVALID_CITY)
        self.assertEqual(verif["confidence"], 0.20)

    def test_historical_aliases(self):
        # 6. Historical aliases: Calcutta for 700001 (exact district match)
        raw_pred = {
            "house_number": "Flat 394",
            "street": "M G Road",
            "city": "Calcutta",
            "state_area": "West Bengal",
            "postal_code": "700001"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        # User city is compatible and directly aliases the district (Kolkata)
        self.assertEqual(resolved["display_city"], "Kolkata")
        self.assertEqual(resolved["raw_city"], "Calcutta")
        self.assertEqual(resolved["routing_district"], "Kolkata")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.CITY_ALIAS)
        self.assertEqual(verif["confidence"], 0.99)

    def test_historical_aliases_nearby(self):
        # 6b. Historical aliases: Calcutta for 700091 (nearby district compatibility)
        raw_pred = {
            "house_number": "Flat 394",
            "street": "M G Road",
            "city": "Calcutta",
            "state_area": "West Bengal",
            "postal_code": "700091"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        # User city is compatible, so resolved to canonical
        self.assertEqual(resolved["display_city"], "Kolkata")
        self.assertEqual(resolved["raw_city"], "Calcutta")
        self.assertEqual(resolved["routing_district"], "North 24 Parganas")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.PIN_COMPATIBLE)
        self.assertEqual(verif["confidence"], 0.95)

    def test_case_insensitivity_and_spacing(self):
        # 7. Case and spacing variations (stripped display_city)
        raw_pred = {
            "house_number": "Flat 394",
            "street": "M G Road",
            "city": "  koLkAtA  ",
            "state_area": "West Bengal",
            "postal_code": "700091"
        }
        res = self.engine.verify_address(raw_pred)
        resolved = res["resolved"]
        verif = res["verification"]
        
        self.assertEqual(resolved["display_city"], "Kolkata")
        self.assertEqual(resolved["raw_city"], "koLkAtA")
        self.assertEqual(verif["resolution_reason"], ResolutionReason.PIN_COMPATIBLE)
        self.assertEqual(verif["confidence"], 0.95)

if __name__ == "__main__":
    unittest.main()
