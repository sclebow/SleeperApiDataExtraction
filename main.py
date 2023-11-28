from sleeperpy import *
import pprint

# Initialize pretty printer
pp = pprint.PrettyPrinter()

# Function to safely perform an API call and handle errors
def safe_api_call(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except Exception as e:
        print(f"API call failed: {e}")
        return None

# Function to find a roster by its ID
def find_roster(roster_id_find, rosters):
    for roster in rosters:
        if roster_id_find == roster.get('roster_id'):
            return roster
    return None

# Function to get head-to-head matchups
def get_head_to_head(team_dicts, matchup_id):
    output = {'team_a': None, 'team_b': None}
    for team_dict in team_dicts:
        if team_dict['matchup_id'] == matchup_id:
            if output['team_a'] is None:
                output['team_a'] = team_dict
            else:
                output['team_b'] = team_dict
                break
    return output if output['team_b'] else None

# Function to calculate the close score factor
def calculate_close_score_factor(head_to_head):
    points_0 = head_to_head['team_a']['points']
    points_1 = head_to_head['team_b']['points']
    point_difference = abs(points_0 - points_1)
    return 1 / (point_difference + 1)

def main():
    league_id = "916453080278011904"  # Replace with your actual league ID

    league = safe_api_call(Leagues.get_league, league_id)
    week = safe_api_call(Leagues.get_state, 'nfl')['week']
    matchups = safe_api_call(Leagues.get_matchups, league_id, week=week)
    users = safe_api_call(Leagues.get_users, league_id)
    rosters = safe_api_call(Leagues.get_rosters, league_id)

    if not (league and week and matchups and users and rosters):
        print("Failed to fetch required data.")
        return

    team_dicts = []

    for matchup in matchups:
        roster_id = matchup['roster_id']
        owner_roster = find_roster(roster_id, rosters)
        if owner_roster:
            owner_id = owner_roster['owner_id']
            display_name = safe_api_call(User.get_user, owner_id)['display_name']
            team_dict = {
                'roster_id': roster_id,
                'owner_id': owner_id,
                'display_name': display_name,
                'matchup_id': matchup['matchup_id'],
                'points': matchup['points']
            }
            team_dicts.append(team_dict)

    scoreboard = []

    for team_dict in team_dicts:
        head_to_head = get_head_to_head(team_dicts, team_dict['matchup_id'])
        if head_to_head and head_to_head not in scoreboard:
            scoreboard.append(head_to_head)

    for head_to_head in scoreboard:
        close_score_factor = calculate_close_score_factor(head_to_head)
        head_to_head['close_score_factor'] = close_score_factor

    pp.pprint(scoreboard)

if __name__ == "__main__":
    main()
