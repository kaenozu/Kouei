from bs4 import BeautifulSoup
import re

class OddsParser:
    @staticmethod
    def parse_2rentan(html_content):
        """
        Parses 2-rentan odds from boatrace.jp HTML.
        Returns a dict: {(boat1, boat2): odds_float}
        """
        soup = BeautifulSoup(html_content, 'lxml')
        odds = {}
        
        # The 2-rentan table has class 'is-w495' or similar.
        # It's structured with boat numbers in the header or first column.
        # Actually, boatrace.jp uses a matrix-like or list-like layout.
        
        # For 2-rentan, it's usually a list of tables.
        tables = soup.find_all('table')
        for table in tables:
            # Check if this table contains odds
            # Usually rows have combinations like "1-2", "1-3", etc.
            rows = table.find_all('tr')
            for row in rows:
                text = row.get_text(strip=True)
                # Look for "X-Y" and a float
                match = re.search(r'(\d)-(\d)\s*([\d.]+)', text)
                if match:
                    b1, b2, val = match.groups()
                    try:
                        odds[(int(b1), int(b2))] = float(val)
                    except:
                        pass
        return odds

    @staticmethod
    def parse_3rentan(html_content):
        """
        Parses 3-rentan odds from boatrace.jp HTML.
        Returns a dict: {(boat1, boat2, boat3): odds_float}
        """
        soup = BeautifulSoup(html_content, 'lxml')
        odds = {}
        
        # 3-rentan is more complex, often split into tables by 1st boat.
        # Matrix layout: 1st boat fixed, 2nd boat vertical, 3rd boat horizontal.
        
        # We'll use a regex search on the whole text as a fallback if structure is hard,
        # but the specific table structure is better.
        
        # Let's try to find all 3-item combinations.
        # Structure: <td> 1-2-3 </td> <td> 12.5 </td>
        # Or often the numbers are in separate spans.
        
        # A robust way is to find all text nodes that look like X-Y-Z and the following number.
        # But boatrace.jp uses specific classes like 'oddsPoint' for the value.
        
        # Let's look for rows or cells containing the pattern.
        # Example pattern: "1-2-3" following by a class like "is-payout1" or "oddsPoint"
        
        # For simplicity in this implementation, we will use a regex-based approach on row text
        # which is surprisingly effective for boatrace.jp's layout.
        
        rows = soup.find_all('tr')
        for row in rows:
            text = " ".join(row.get_text(" ", strip=True).split())
            # Match pattern: "1 - 2 - 3 12.5"
            matches = re.findall(r'(\d)\s*-\s*(\d)\s*-\s*(\d)\s*([\d.]+)', text)
            for m in matches:
                b1, b2, b3, val = m
                try:
                    odds[(int(b1), int(b2), int(b3))] = float(val)
                except:
                    pass
        return odds
