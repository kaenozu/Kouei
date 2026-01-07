from bs4 import BeautifulSoup
import re
import pandas as pd

class ProgramParser:
    @staticmethod
    def parse_start_times(html_content):
        """
        Extracts all 12 race start times from a program HTML.
        Returns a dict {race_no: start_time_str}
        """
        soup = BeautifulSoup(html_content, 'lxml')
        times = {}
        # Find the table containing "締切予定時刻"
        rows = soup.find_all('tr')
        for row in rows:
            tds = row.find_all(['td', 'th'])
            text = row.get_text()
            if "締切予定時刻" in text:
                # The subsequent tds should be the times for R1 to R12
                time_tds = row.find_all('td', recursive=False)
                # In the layout, td[0] is often the label (締切予定時刻)
                # We need R1 to R12.
                # Let's be robust: find all text that looks like HH:MM
                time_strings = re.findall(r'\d{2}:\d{2}', row.get_text())
                for i, ts in enumerate(time_strings, 1):
                    times[i] = ts
                break
        return times

    @staticmethod
    def parse_race_name(html_content):
        """
        Extracts the race name (e.g., "予選") from a program HTML.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        title_node = soup.find('h3', class_='title16_titleDetail__add2020')
        if title_node:
            race_name = title_node.get_text(strip=True).replace('\u3000', ' ')
            return " ".join(race_name.split())
        return ""

    @staticmethod
    def parse(html_content, date_str, jyo_cd, race_no):
        """
        Parses program HTML (Entry List).
        Returns a DataFrame with one row per boat (6 rows total).
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract start time for THIS race
        start_times = ProgramParser.parse_start_times(html_content)
        start_time = start_times.get(race_no)

        # Extract Race Name
        race_name = ProgramParser.parse_race_name(html_content)

        data = []
        
        # The program table usually has 6 blocks for 6 boats
        # We can find them by looking for 'is-boatColor1' to 'is-boatColor6'
        # inside the table bodies.
        
        # There are multiple tbodies, each containing one racer's info (and potentially empty rows).
        tbodies = soup.find_all('tbody', class_='is-fs12')
        
        for tbody in tbodies:
            # 1. Boat Number (Wakuban)
            boat_node = tbody.find('td', class_=re.compile(r'is-boatColor\d'))
            if not boat_node:
                continue
            
            boat_no = int(boat_node.get_text(strip=True))
            
            # 2. Racer Info
            # The racer name and ID are in the next td
            # There might be multiple links with toban (image and name). 
            # We want the one with text.
            profile_links = tbody.find_all('a', href=re.compile(r'toban=\d+'))
            racer_name = ""
            racer_id = ""
            
            for link in profile_links:
                href = link['href']
                match = re.search(r'toban=(\d+)', href)
                if match:
                    racer_id = match.group(1) # ID is valid from any link
                
                text = link.get_text(strip=True)
                if text:
                    racer_name = text.replace('\u3000', ' ') # Normalize spaces
                    break # Found the name
            
            # 3. Motor and Boat stats
            # These are in the subsequent tds.
            # Rowspan is usually 4.
            # We need to rely on the column order.
            # Col 1: Boat No
            # Col 2: Photo
            # Col 3: Profile (ID, Name, Branch, Weight, Age)
            # Col 4: F/L
            # Col 5: Nationwide Win Rate
            # Col 6: Local Win Rate
            # Col 7: Motor stats
            # Col 8: Boat stats
            
            # Let's find all 'td' with rowspan='4' in the first tr of the tbody
            first_tr = tbody.find('tr')
            tds = first_tr.find_all('td', recursive=False)
            
            # Depending on layout, indices might vary.
            # Based on inspection:
            # td[0]: Boat No
            # td[1]: Photo
            # td[2]: Profile
            # td[3]: F/L
            # td[4]: Nationwide stats
            # td[5]: Local stats
            # td[6]: Motor stats (No, 2ren, 3ren)
            # td[7]: Boat stats
            
            # Nationwide stats (Win rate is usually the first number)
            nationwide_text = tds[4].get_text(" ", strip=True) if len(tds) > 4 else ""
            nationwide_parts = nationwide_text.split()
            racer_win_rate = nationwide_parts[0] if len(nationwide_parts) > 0 else None
            
            # Racer Rank (in td[2])
            # Content examples: "4144 / A2", "埼玉 / 52kg" ... often mixed.
            # Usually strict format: ID / Rank / Branch / Weight / Age
            # But get_text(" ", strip=True) might merge them.
            # Looking for A1, A2, B1, B2 pattern.
            profile_text = tds[2].get_text(" ", strip=True) if len(tds) > 2 else ""
            match_rank = re.search(r'(A1|A2|B1|B2)', profile_text)
            racer_rank = match_rank.group(1) if match_rank else None

            # Average ST (in td[3])
            # Content examples: "F0 L0 0.19"
            fl_text = tds[3].get_text(" ", strip=True) if len(tds) > 3 else ""
            # looking for 0.XX
            match_st = re.search(r'(\d\.\d{2})', fl_text)
            average_st = float(match_st.group(1)) if match_st else None
            

            motor_text = tds[6].get_text(" ", strip=True) if len(tds) > 6 else ""
            motor_parts = motor_text.split()
            motor_no = motor_parts[0] if len(motor_parts) > 0 else None
            motor_2ren = motor_parts[1] if len(motor_parts) > 1 else None
            
            boat_text = tds[7].get_text(" ", strip=True) if len(tds) > 7 else ""
            boat_parts = boat_text.split()
            boat_hull_no = boat_parts[0] if len(boat_parts) > 0 else None
            boat_2ren = boat_parts[1] if len(boat_parts) > 1 else None
            
            data.append({
                'date': date_str,
                'jyo_cd': jyo_cd,
                'race_no': race_no,
                'boat_no': boat_no, # Wakuban (1-6)
                'racer_id': racer_id,
                'racer_name': racer_name,
                'racer_rank': racer_rank,
                'average_st': average_st,
                'racer_win_rate': racer_win_rate,
                'motor_no': motor_no,
                'motor_2ren': motor_2ren,
                'boat_hull_no': boat_hull_no,
                'boat_2ren': boat_2ren,
                'start_time': start_time,
                'race_name': race_name
            })
            
        return pd.DataFrame(data)

class ResultParser:
    @staticmethod
    def parse(html_content, date_str, jyo_cd, race_no):
        """
        Parses result HTML.
        Returns a DataFrame with race results (Ranking).
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        data = []
        
        # Find the result table
        # It usually has headers: 着, 枠, ボートレーサー
        # We can look for the specific table structure.
        
        # The structure seen in file view:
        # <table class="is-w495">...<thead>...<th>着</th>...
        
        tables = soup.find_all('table', class_='is-w495')
        result_table = None
        for t in tables:
            headers = [th.get_text(strip=True) for th in t.find_all('th')]
            if '着' in headers and '枠' in headers:
                result_table = t
                break
        
        if result_table:
            # Parse key-value for payouts
            payouts = {} # key: bet_type, value: money (int)
            # Find all payout rows
            # Payouts are in the same or separate table? 
            # In the file viewed, they are in a grid with class "grid is-type2" -> "grid_unit" -> "table1"
            # It seems the result table (ranks) is one table, and payout table is another.
            # We need to find the payout table.
            
            # The payout table has '勝式', '組番', '払戻金' headers.
            payout_table = None
            for t in tables:
                headers = [th.get_text(strip=True) for th in t.find_all('th')]
                if '勝式' in headers and '払戻金' in headers:
                    payout_table = t
                    break

            if payout_table:
                # Iterate rows to find Tansho
                # Structure: tbody -> tr -> td "単勝"
                tbodies = payout_table.find_all('tbody')
                for tbody in tbodies:
                    tr = tbody.find('tr')
                    if not tr: continue
                    label_td = tr.find('td')
                    label = label_td.get_text(strip=True)
                    
                    if label == '単勝':
                         # The payout value is in the 3rd td (index 2) usually, but check colspan
                         # td[0]: label (rowspan)
                         # td[1]: kumiban
                         # td[2]: money
                         tds = tr.find_all('td')
                         # Depending on rowspan layout, money is usually identifiable by class 'is-payout1'
                         money_span = tr.find('span', class_='is-payout1')
                         if money_span:
                             money_text = money_span.get_text(strip=True).replace('¥', '').replace(',', '')
                             try:
                                 payouts['tansho'] = int(money_text)
                             except:
                                 pass
            
            rows = result_table.find_all('tbody')
            for row in rows:
                tr = row.find('tr')
                if not tr: continue
                cols = tr.find_all('td')
                if len(cols) < 3: continue
                
                rank_text = cols[0].get_text(strip=True)
                # Handle special ranks like '欠', '失', '不'
                try:
                    rank = int(rank_text)
                except:
                    rank = rank_text 
                
                waku_text = cols[1].get_text(strip=True)
                
                row_data = {
                    'date': date_str,
                    'jyo_cd': jyo_cd,
                    'race_no': race_no,
                    'boat_no': int(waku_text),
                    'rank': rank
                }
                
                if rank == 1 and 'tansho' in payouts:
                    row_data['tansho'] = payouts['tansho']
                else:
                    row_data['tansho'] = 0
                    
                data.append(row_data)
        
        return pd.DataFrame(data)

class BeforeInfoParser:
    @staticmethod
    def parse(html_content, date_str, jyo_cd, race_no):
        """
        Parse Before Information HTML (chokuzen)
        Extracts: Exhibition Time, Tilt, Weather, Wind, Wave
        """
        soup = BeautifulSoup(html_content, 'lxml')
        data = []
        
        # 1. Weather Info
        weather_data = {
            'temperature': None,
            'weather': None,
            'wind_speed': None,
            'wind_direction': None,
            'water_temperature': None,
            'wave_height': None
        }
        
        weather_unit = soup.find('div', class_='weather1')
        if weather_unit:
            # Temperature
            temp_node = weather_unit.find('div', class_='is-direction')
            if temp_node:
                val = temp_node.find('span', class_='weather1_bodyUnitLabelData')
                if val:
                    weather_data['temperature'] = val.get_text(strip=True).replace('℃', '')

            # Weather (Image class)
            w_node = weather_unit.find('div', class_='is-weather')
            if w_node:
                img_node = w_node.find('p', class_='weather1_bodyUnitImage')
                if img_node:
                    # Extract class like 'is-weather2'
                    classes = img_node.get('class', [])
                    for c in classes:
                        if c.startswith('is-weather') and c != 'weather1_bodyUnitImage':
                            weather_data['weather'] = c.replace('is-weather', '')
                            break
            
            # Wind Speed
            wind_node = weather_unit.find('div', class_='is-wind')
            if wind_node:
                val = wind_node.find('span', class_='weather1_bodyUnitLabelData')
                if val:
                    weather_data['wind_speed'] = val.get_text(strip=True).replace('m', '')

            # Wind Direction
            wd_node = weather_unit.find('div', class_='is-windDirection')
            if wd_node:
                img_node = wd_node.find('p', class_='weather1_bodyUnitImage')
                if img_node:
                    classes = img_node.get('class', [])
                    for c in classes:
                        if c.startswith('is-wind') and c != 'weather1_bodyUnitImage':
                            weather_data['wind_direction'] = c.replace('is-wind', '')
                            break

            # Water Temperature
            wt_node = weather_unit.find('div', class_='is-waterTemperature')
            if wt_node:
                val = wt_node.find('span', class_='weather1_bodyUnitLabelData')
                if val:
                    weather_data['water_temperature'] = val.get_text(strip=True).replace('℃', '')

            # Wave Height
            wave_node = weather_unit.find('div', class_='is-wave')
            if wave_node:
                val = wave_node.find('span', class_='weather1_bodyUnitLabelData')
                if val:
                    weather_data['wave_height'] = val.get_text(strip=True).replace('cm', '')


        # 2. Racer Info (Exhibition Time, Tilt)
        # Main table is is-w748
        table = soup.find('table', class_='is-w748')
        if table:
            tbodies = table.find_all('tbody', class_='is-fs12')
            for tbody in tbodies:
                # Boat No is in td with class is-boatColorX
                boat_node = tbody.find('td', class_=re.compile(r'is-boatColor\d'))
                if not boat_node:
                    continue
                boat_no = int(boat_node.get_text(strip=True))

                # Structure inside tbody > tr
                # td 0: boat waku (rowspan 4)
                # td 1: photo (rowspan 4)
                # td 2: name (rowspan 4)
                # td 3: weight (rowspan 2)
                # td 4: exhibition time (rowspan 4)
                # td 5: tilt (rowspan 4)
                # ...
                
                # Careful: The first tr contains the rowspan elements
                tr = tbody.find('tr')
                tds = tr.find_all('td', recursive=False)
                
                # Index might shift depending on exact layout, but usually fixed.
                # Let's inspect based on our sample.
                # 0: 1 (rowspan 4)
                # 1: img (rowspan 4)
                # 2: name (rowspan 4)
                # 3: weight
                # 4: exhibition time
                # 5: tilt
                
                exhibition_time = None
                tilt = None
                
                if len(tds) > 5:
                    exhibition_time = tds[4].get_text(strip=True)
                    tilt = tds[5].get_text(strip=True)
                
                row_data = {
                    'date': date_str,
                    'jyo_cd': jyo_cd,
                    'race_no': race_no,
                    'boat_no': boat_no,
                    'exhibition_time': exhibition_time,
                    'tilt': tilt
                }
                # Merge weather info into every row
                row_data.update(weather_data)
                data.append(row_data)

        return pd.DataFrame(data)
