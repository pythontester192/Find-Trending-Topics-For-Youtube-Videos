import requests, sys, time, os, argparse
snippet_features = ["title",
                    "publishedAt",
                    "channelId",
                    "channelTitle",
                    "categoryId"]
unsafe_characters = ['\n', '"']
header = ["video_id"] + snippet_features + ["trending_date", "tags", "view_count",
                                            "comment_count", "thumbnail_link", "description"]
def setup(api_path, code_path):
    with open(api_path, 'r') as file:
        api_key = file.readline()
    with open(code_path) as file:
        country_codes = [x.rstrip() for x in file]
    return api_key, country_codes
def prepare_feature(feature):
    for ch in unsafe_characters:
        feature = str(feature).replace(ch, "")
    return f'"{feature}"'
def api_request(page_token, country_code):
    request_url = f"https://www.googleapis.com/youtube/v3/videos?part=id,statistics,snippet{page_token}chart=mostPopular&regionCode={country_code}&maxResults=50&key={api_key}"
    request = requests.get(request_url)
    if request.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit()
    return request.json()
def get_tags(tags_list):
    return prepare_feature("|".join(tags_list))
def get_videos(items):
    lines = []
    for video in items:
        if "statistics" not in video:
            continue
        video_id = prepare_feature(video['id'])
        snippet = video['snippet']
        statistics = video['statistics']
        features = [prepare_feature(snippet.get(feature, "")) for feature in snippet_features]
        description = snippet.get("description", "")
        thumbnail_link = snippet.get("thumbnails", dict()).get("default", dict()).get("url", "")
        trending_date = time.strftime("%y.%d.%m")
        tags = get_tags(snippet.get("tags", ["[none]"]))
        view_count = statistics.get("viewCount", 0)
        if 'likeCount' in statistics and 'dislikeCount' in statistics:
            likes = statistics['likeCount']
            dislikes = statistics['dislikeCount']
        if 'commentCount' in statistics:
            comment_count = statistics['commentCount']
        else:
            comment_count = 0
        line = [video_id] + features + [prepare_feature(x) for x in [trending_date, tags, view_count,
                                                                       comment_count, thumbnail_link,description]]
        lines.append(",".join(line))
    return lines
def get_pages(country_code, next_page_token="&"):
    country_data = []
    while next_page_token is not None:
        video_data_page = api_request(next_page_token, country_code)
        
        if video_data_page.get('error'):
            print(video_data_page['error'])
        next_page_token = video_data_page.get("nextPageToken", None)
        next_page_token = f"&pageToken={next_page_token}&" if next_page_token is not None else next_page_token
        items = video_data_page.get('items', [])
        country_data += get_videos(items)
    return country_data
def write_to_file(country_code, country_data):
    print(f"Writing {country_code} data to file...")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(f"{output_dir}/{time.strftime('%y.%d.%m')}_{country_code}_videos.csv", "w+", encoding='utf-8') as file:
        for row in country_data:
            file.write(f"{row}\n")
def get_data():
    for country_code in country_codes:
        country_data = [",".join(header)] + get_pages(country_code)
        write_to_file(country_code, country_data)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--key_path', help='Path to the file containing the api key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--country_code_path', help='Path to the file containing the list of country codes to scrape, by default will use country_codes.txt in the same directory', default='country_codes.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='output/')
    args = parser.parse_args()
    output_dir = args.output_dir
    api_key, country_codes = setup(args.key_path, args.country_code_path)

    get_data()