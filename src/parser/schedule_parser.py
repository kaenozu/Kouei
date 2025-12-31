from bs4 import BeautifulSoup
import re

class ScheduleParser:
    @staticmethod
    def parse(html_content):
        """
        Parses the schedule page HTML and returns a list of active stadium codes (jyo_cd).
        """
        soup = BeautifulSoup(html_content, 'lxml')
        jyo_codes = []
        
        # Look for links to raceindex
        # Example: /owpc/pc/race/raceindex?jcd=02&hd=20241201
        links = soup.find_all('a', href=re.compile(r'/owpc/pc/race/raceindex\?jcd=(\d+)'))
        
        for link in links:
            href = link['href']
            match = re.search(r'jcd=(\d+)', href)
            if match:
                jyo_codes.append(match.group(1))
        
        return sorted(list(set(jyo_codes)))


def parse_today_races(html_content):
    """
    Parses the today's races page HTML and returns a list of races.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    races = []
    
    # This is a simplified implementation
    # In a real implementation, you would parse the actual race data from the HTML
    # For now, we'll return an empty list to avoid errors
    return races
