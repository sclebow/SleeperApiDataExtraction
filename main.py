from sleeperpy import *
import pprint
import sleeper_wrapper
import pickle
from datetime import date
import requests

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

# Function to get player ids from a roster_id
def get_player_ids(roster_id, matchups):
    output = None

    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            output = matchup['players']

    return output

# Function to get starter ids from a roster_id
def get_starter_ids(roster_id, matchups):
    output = None

    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            output = matchup['starters']

    return output

# Function to get all players
# Only connects to Sleeper once per day
def get_all_players():
    today_string = date.today().strftime("%y%m%d")
    try:
        with open(f'players_data/{today_string}_players', 'rb') as f:
            players_dict = pickle.load(f)
            return players_dict
    except:
        players_wrapper = sleeper_wrapper.Players()
        players_dict = players_wrapper.get_all_players()
        with open(f'players_data/{today_string}_players', 'wb') as f:
            pickle.dump(players_dict, f)
        return players_dict
    
def find_matchup_roster(matchups, matchup_id, roster_id):
    for matchup in matchups:
        matchup_id_match = matchup['matchup_id']
        roster_id_match = matchup['roster_id']

        if matchup_id_match == matchup_id and roster_id_match == roster_id:
            return matchup
    return None

def find_matchup_starter_points(matchup, player_id):
    for starter, starter_points in zip(matchup['starters'], matchup['starters_points']):
        if starter == player_id:
            return starter_points
    return None

def construct_team_players(starter_ids, matchup, players):
    team_players = []
    players_keys = ['first_name', 'last_name', 'full_name', 'team', 'player_id', 'position', 'number']
    
    for player_id in starter_ids:
        player = {key: players[player_id][key] for key in players_keys}
        player['points'] = find_matchup_starter_points(matchup, player_id)
        team_players.append(player)

    return team_players

def main():
    league_id = "916453080278011904"  # Replace with your actual league ID

    league = safe_api_call(Leagues.get_league, league_id)
    week = safe_api_call(Leagues.get_state, 'nfl')['week']
    matchups = safe_api_call(Leagues.get_matchups, league_id, week=week)
    users = safe_api_call(Leagues.get_users, league_id)
    rosters = safe_api_call(Leagues.get_rosters, league_id)    
    players = get_all_players()

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

        team_a_starter_ids = get_starter_ids(head_to_head['team_a']['roster_id'], matchups)
        team_a_matchup = find_matchup_roster(matchups, head_to_head['team_a']['matchup_id'], head_to_head['team_a']['roster_id'])

        head_to_head['team_a']['players'] = construct_team_players(team_a_starter_ids, team_a_matchup, players)

        team_b_starter_ids = get_starter_ids(head_to_head['team_b']['roster_id'], matchups)
        team_b_matchup = find_matchup_roster(matchups, head_to_head['team_b']['matchup_id'], head_to_head['team_b']['roster_id'])

        head_to_head['team_b']['players'] = construct_team_players(team_b_starter_ids, team_b_matchup, players)

        pp.pprint(head_to_head)
        break
 
if __name__ == "__main__":
    main()
