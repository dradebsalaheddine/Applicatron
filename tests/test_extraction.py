import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from mail_analysis import extract,recruitment_hint,obvious_bulk
class ExtractionTests(unittest.TestCase):
 def test_company_prefix(self):
  self.assertEqual(extract('Acme - Votre candidature pour le poste de Analyste GRC','')['company'],'Acme')
 def test_commas(self):
  self.assertEqual(extract('Votre candidature au poste de Consultant Gouvernance, Risques et contrôle','')['role'],'Consultant Gouvernance, Risques et contrôle')
 def test_false_company(self):
  self.assertEqual(extract('Your application : Stage – Assistant Engineer – ABC123','')['company'],'')
 def test_recovery_hints(self):
  for subject in ['Demande de stage PFE','Follow-Up on Engineer Application','We received your project for the Pre-sales Engineer Intern position']:
   self.assertTrue(recruitment_hint(subject))
  self.assertTrue(obvious_bulk('There are 10 jobs matching your criteria'))
