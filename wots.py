# python3 wots.py /cygdrive/c/Games/World_of_Tanks/replays/
import os
import sys
import json
import argparse
import datetime
from os import walk

# 統計結果
total_stats       = {}
ver_total_stats   = {}
ver_map_stats     = {}
player_clan_stats = {}
enemy_clan_stats  = {}
filter_names = None
filter_vers  = None
filter_hours = None
filter_days  = None

# メイン処理
def main():
	global filter_names, filter_vers, filter_days, filter_hours
	parser = argparse.ArgumentParser()
	parser.add_argument("dir", help=".wotreplay directory")
	parser.add_argument("-n",  dest="names", help="filter team member names (comma separeted, no space)")
	parser.add_argument("-v",  dest="vers",  type=int, help="filter wot version (1=new version, 2=new and last version, ...) ")
	parser.add_argument("-o",  dest="hours", type=int, help="filter hours")
	parser.add_argument("-d",  dest="days",  type=int, help="filter days")
	args = parser.parse_args()
	filter_names = args.names
	filter_vers  = args.vers
	filter_hours = args.hours
	filter_days  = args.days

	process_wotreplay_dir(args.dir, calc_statistics)

	disp("総合", total_stats)
	disp("バージョン別", ver_total_stats)
	disp("マップ別", ver_map_stats)
	for clan in ("H-666", "PZSRL", "SDRHB", "BLINE", "ZHAN"):
		if clan in player_clan_stats or clan in enemy_clan_stats:
			print("")
		if clan in player_clan_stats:
			disp("[" + clan + "]が味方なら勝つる!", player_clan_stats[clan])
		if clan in enemy_clan_stats:
			disp("[" + clan + "]が敵なら勝つる!", enemy_clan_stats[clan])

# 統計を計算
def calc_statistics(result):
	global filter_names, filter_vers, filter_days, filter_hours
	if filter_names != None:
		names = filter_names.split(",")
		for name in names:
			if (name in result["playerTeamNames"]) == False:
				return
	if filter_vers != None:
		if len(ver_total_stats) >= filter_vers and (result["ver"] in ver_total_stats) == False:
			return
	if filter_days != None or filter_hours != None:
		now_time   = datetime.datetime.now()
		file_time  = result["dateTime"]
		delta_time = now_time - file_time
		if filter_hours != None and (delta_time.days >= 1 or delta_time.seconds > (3600 * filter_hours)):
			return
		if filter_days != None and delta_time.days >= filter_days:
			return

	ver = result["ver"]
	map = result["mapDisplayName"]
	win = result["win"]

	# 全統計
	count(total_stats, win)
	
	# バージョン別全統計
	if (ver in ver_total_stats) == False:
		ver_total_stats[ver] = {}
	count(ver_total_stats[ver], win)

	# バージョン別マップ別統計
	if (ver in ver_map_stats) == False:
		ver_map_stats[ver] = {}
	if (map in ver_map_stats[ver]) == False:
		ver_map_stats[ver][map] = {}
	count(ver_map_stats[ver][map], win)

	# このクランが味方にいたら勝てるんじゃあ
	for clan in result["playerTeamClans"]:
		if (clan in player_clan_stats) == False:
			player_clan_stats[clan] = {}
		count(player_clan_stats[clan], win)

	# このクランには勝ってる
	for clan in result["enemyTeamClans"]:
		if (clan in enemy_clan_stats) == False:
			enemy_clan_stats[clan] = {}
		count(enemy_clan_stats[clan], win)

# カウント
def count(dict, win):
	if ("win" in dict) == False:
		dict["win"] = 0
	if ("lose" in dict) == False:
		dict["lose"] = 0
	if ("total" in dict) == False:
		dict["total"] = 0
	if win:
		dict["win"] += 1
	else:
		dict["lose"] += 1
	dict["total"] += 1

# 表示
def disp(title, dict, indent = 0, indent_str = "    "):
	print(indent_str * indent + title + ":")
	if "win" in dict and "lose" in dict and "total" in dict:
		win   = dict["win"]
		lose  = dict["lose"]
		total = dict["total"]
		wr    = win / total * 100.0
		print("{0}勝率 {1:3.1f}% (win:{2:2d}, lose:{3:2d}, total:{4:2d})".format(indent_str * (indent + 1), wr, win, lose, total))
	else:
		items = sorted(dict.items(), key=lambda x: x[1]["total"] if "total" in x[1] else x[0])
		items.reverse()
		for data in items:
			disp(data[0], data[1], indent + 1)

################################################################################
################################################################################
################################################################################

# リプレイディレクトリを処理
def process_wotreplay_dir(dir, callback):
	files = []
	for (dirpath, dirnames, filenames) in walk(dir):
		filenames = [dirpath + f for f in filenames if f.endswith(".wotreplay") == True]
		files.extend(filenames)
	files.reverse()
	for file in files:
		process_wotreplay_file(file, callback)

# リプレイファイルを処理
def process_wotreplay_file(file, callback):
	with open(file, "rb") as f:
		magic = get_ulong(f, 4)
		if magic != 288633362:
			print("file '" + file + "' is not wotreplay file has wrong magic number (" + str(magic) + ").", file=sys.stderr);
			return
		winning_team_number = get_ulong(f, 1)
		get_ulong(f, 3)

		first_chunk_size = get_ulong(f, 4)
		first_chunk = get_json(f, first_chunk_size)
		player_name = first_chunk["playerName"]
		vehicles    = first_chunk["vehicles"]

		teams = {1:[], 2:[]}
		for k, v in vehicles.items():
			teams[v["team"]].append((v["name"], v["clanAbbrev"], v["vehicleType"]))
			if v["name"] == player_name:
				player_team_number = v["team"]

		player_team = teams[1]
		enemy_team  = teams[2]
		if player_team_number == 2:
			player_team = teams[2]
			enemy_team  = teams[1]

		result = {
			"ver":             first_chunk["clientVersionFromExe"],
			"dateTime":        datetime.datetime.strptime(first_chunk["dateTime"], "%d.%m.%Y %H:%M:%S"),
			"mapName":         first_chunk["mapName"],
			"mapDisplayName":  first_chunk["mapDisplayName"],
			"rule":            first_chunk["gameplayID"],
			"playerName":      player_name,
			"win":             (winning_team_number == player_team_number),
			"playerTeam":      player_team,
			"enemyTeam":       enemy_team,
			"playerTeamNames": [member[0] for member in player_team],
			"enemyTeamNames":  [member[0] for member in enemy_team],
			"playerTeamClans": list(set([member[1] for member in player_team if member[1] != ""])),
			"enemyTeamClans":  list(set([member[1] for member in enemy_team if member[1] != ""])),
		}
		callback(result)

# 符号なし整数を取得
def get_ulong(f, n):
	return int.from_bytes(f.read(n), byteorder='little', signed=False)

# 文字列を取得
def get_string(f, n):
	return f.read(n).decode(encoding="UTF-8")

# Json 文字列をオブジェクトとして取得
def get_json(f, n):
	return json.loads(get_string(f, n))

################################################################################
################################################################################
################################################################################
main()

