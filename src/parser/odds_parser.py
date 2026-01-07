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
        # Updated logic for matrix table (Boat - Odds pairs in columns)
        # Table has 12 columns (6 pairs of Boat+Odds)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                tds = row.find_all('td')
                # 6 boats * 2 columns = 12 columns. Some rows might be shorter?
                # We iterate pairs.
                
                for i in range(0, len(tds), 2):
                    if i + 1 >= len(tds):
                        break
                    
                    b_txt = tds[i].get_text(strip=True)
                    o_txt = tds[i+1].get_text(strip=True)
                    
                    if b_txt.isdigit() and re.match(r'^\d+(\.\d+)?$', o_txt):
                        try:
                            opponent = int(b_txt)
                            val = float(o_txt)
                            
                            # Which First Boat is this?
                            # Columns 0-1 -> Boat 1
                            # Columns 2-3 -> Boat 2
                            # ...
                            first_boat = (i // 2) + 1
                            
                            if 1 <= first_boat <= 6:
                                odds[(first_boat, opponent)] = val
                        except:
                            pass
        
        # Fallback to regex if empty (maybe some stadiums differ?)
        if not odds:
             for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    text = row.get_text(strip=True)
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
