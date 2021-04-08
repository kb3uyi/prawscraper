# prawScraper.py

import praw
import json
import sys
import argparse
from tqdm import tqdm
import requests
import math
from os import path
from urllib.parse import urlparse

class prawScraper:
    # Constructor method with instance variables allowedFiletypes and agedebug
    def __init__(self, allowedFiletypes, debug):
        self.allowedFiletypes = allowedFiletypes
        self.debug = debug

    def scrape(self, subreddit, limit, verbose, downloadDir, authFile, nsfw, unsave):
        """Function to loop over the saved reddit posts.

        Arguments:
            subreddit {string} -- subreddit to check (null for all subreddits)
            limit {int} -- limit of posts to fetch in a single call
            verbose {boolean} -- set output verbosity
            downloadDir {string} -- destination of saved files
            authFile {string} -- path to the authentication file
            nsfw {string} -- set nsfw inclusion: none, include, exclusive
            unsave {boolean} -- should processed posts be unsaved
        """
        with open(authFile) as f:
            auth_data = json.load(f)

        # ? things not in the JSON file are null right?
        # TODO add the check that username and password should be prompted.
        # ! even if the username and password are prompted, authfile is needed for client and secret
        reddit = praw.Reddit(client_id      = auth_data['client_id'],
                             client_secret  = auth_data['client_secret'],
                             password       = auth_data['password'],
                             user_agent     = auth_data['user_agent'],
                             username       = auth_data['username']
                             )

        if verbose:
            print(reddit.user.me())
            print("Download Directory: " + downloadDir)

        # set read only mode
        # reddit.read_only = True

        subreddit_name  = subreddit
        saved_limit     = limit
        subreddit_selected = True

        if subreddit_name is None or subreddit_name == "none":
            subreddit_selected = False
        else:
            subreddit_selected = True
            selected_sub = reddit.subreddit(subreddit_name)
            if verbose:
                print("Selected subredit name: " + selected_sub.name)
                print("Selected subredit id: " + selected_sub.id)

        if saved_limit is None:
            saved = reddit.user.me().saved()
        else:
            saved = reddit.user.me().saved(limit=saved_limit)

        for post in saved:
            try:
                if isinstance(post, praw.models.Submission):
                    if subreddit_selected == True:
                        if post.subreddit_id == selected_sub.name:
                            prawScraper.process_post(post, verbose, downloadDir, nsfw, unsave)
                    else:
                        prawScraper.process_post(self, post, verbose, downloadDir, nsfw, unsave)
            except AttributeError as err:
                print(err)

    def process_post(self, post, verbose, downloadDir, nsfw, unsave):
        """Function to process individual posts from the set of fetched posts

        Arguments:
            post {string} -- fetched post URL
            verbose {boolean} -- set output verbosity
            downloadDir {string} -- destination of saved files
            authFile {string} -- path to the authentication file
            nsfw {string} -- set nsfw inclusion: none, include, exclusive
            unsave {boolean} -- should processed posts be unsaved
        Returns:
            None
        """
        if nsfw == "none" and post.over_18:
            return # This post cannot be included in a worksafe run
        if nsfw == "exclusive" and not post.over_18:
            return # This post cannot be indluded in a non-worsafe run
        # The 'included' case is a free for all
        
        # submission link is at post.url, separate the extension
        urlParts =  urlparse(post.url) # Parse URL into parts
        filename =  path.basename(urlParts.path) # basename is the filename and extension
        extension = path.splitext(filename)[1].split("?")[0] # split for extension
        
        if extension in self.allowedFiletypes:
            # filetype allowed, download
            if verbose:
                print(post.url + " : " + filename)

            # Call helper method for code reuse
            prawScraper.download_file(post.url, downloadDir)

            if unsave:
                if verbose:
                    print(post.title + " was unsaved.")
                post.unsave()
        elif self.debug:
            print("REJECTED - " + post.url + " : " + filename)
        else:
            prawScraper.gallery_process(self, post, verbose, downloadDir, unsave)
            
    def download_file(downloadURL, downloadDir):
        """Download a file once the URL is completely set.

        Arguments:
            downloadURL {string} -- source URL
            downloadDir {string} -- destination of saved files
        Returns:
            None
        """
        # re-split for the file name
        urlParts =  urlparse(downloadURL) # Parse URL into parts
        filename =  path.basename(urlParts.path) # basename is the filename and extension

        # Streaming, so we can iterate over the response.
        # To save to a relative path: r = requests.get(url)
        r = requests.get(downloadURL, stream=True)

        if not path.exists(downloadDir + filename):
            with open(downloadDir + filename, 'wb') as f:
                f.write(r.content)

            # Total size in bytes.
            total_size = int(r.headers.get('content-length', 0))
            block_size = 1024
            wrote = 0
            with open('output.bin', 'wb') as f:
                for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size//block_size) , unit='KB', unit_scale=True):
                    wrote = wrote  + len(data)
                    f.write(data)
            if total_size != 0 and wrote != total_size:
                print("ERROR, something went wrong")
        else:
            print("SKIPPED, file exists - " + filename)

    def gallery_process(self, post, verbose, downloadDir, unsave):
        """Secondary processing of the URL
        The first method grabs any direct links to an allowed extension, but some urls don't link directly to content.
        For example, reddit has new galleries that only show image URLs in the metadata.
        This helper method will scrape known galleries if I have explicitly written a case to handle it.
        NSFW posts have already been included or excluded because of the parent method filtering on them.

        Arguments:
            verbose {boolean} -- set output verbosity
            downloadDir {string} -- destination of saved files
            unsave {boolean} -- should processed posts be unsaved
        Returns:
            None
        """
        if post.url.find("reddit.com/gallery/") != -1:
            downloads = 0
            if verbose:
                print("reddit gallery\t" + str(post.url))
            gallery_data = post.media_metadata
            for media_id in gallery_data:
                image_data = post.media_metadata[media_id]
                if image_data['e'] == 'Image':
                    if len(image_data['p']) > 0 : # 'p' sub-list of URLs
                        media_url = image_data['p'][-1]['u']
                        if verbose:
                            print("p:\t" + media_url)
                        prawScraper.download_file(media_url, downloadDir)
                        downloads += 1
            if unsave and downloads > 0:
                if verbose:
                    print(post.title + " was unsaved.")
                post.unsave()


def main(argv):
        """Main function for fetching saved reddit posts

        Arguments:
            argv {list of string} -- command line arguments
        """
        parser = argparse.ArgumentParser(description='Process saved reddit posts using \'authenitcation.json\' account info.')
        parser.add_argument("-a", "--authfile", dest="authfile", default="./authentication.json",
                            help="json file for reddit authentication", metavar="AUTH_FILE")
        parser.add_argument("-f", "--filetypes", dest="typesJSON", default="./filetypes.json",
                            help="json file for filetypes to download", metavar="TYPES_JSON")
        parser.add_argument("-d", "--directory", dest="directory", required=True,
                            help="directory to save images to", metavar="DOWNLOAD_DIR")
        parser.add_argument("-s", "--subreddit", dest="subreddit",
                            help="subreddit to filter on, optional", metavar="SUBREDDIT")
        parser.add_argument("-l", "--limit", dest="limit", type=int,
                            help="limit number of saved posts", metavar="SAVED_LIMIT")
        parser.add_argument("-v", "--verbose", help="increase output verbosity",
                            action="store_true")
        parser.add_argument("-nsfw", "--not_safe_for_work", dest="nsfw", default="none",
                            help="show nsfw posts: none, include, exclusive", metavar="NSFW_FLAG")
        parser.add_argument("-u", "--unsave", help="unsave the posts that get downloaded", action="store_true")
        parser.add_argument("--debug", dest="debug", help=argparse.SUPPRESS, action="store_true")

        args = parser.parse_args()
        # TODO: add an argument to prompt for credentials. leave authfile for client and secret.
        # TODO: add an argument for additional file types.

        with open(args.typesJSON) as typesFile:
            types_data = json.load(typesFile)

        if  args.debug:
            print("DEBUG: auth file = " + args.authfile)
            print("DEBUG: nsfw = " + args.nsfw)
            print("DEBUG: unsave = " + str(args.unsave))
            print("DEBUG: types file = " + args.typesJSON)

        scraperObj = prawScraper(types_data['allowedFiletypes'], args.debug)
        scraperObj.scrape(args.subreddit, args.limit, args.verbose, args.directory, args.authfile, args.nsfw, args.unsave)

if __name__ == "__main__":
   """call class main"""
   main(sys.argv[1:])