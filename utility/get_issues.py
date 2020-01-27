"""Get selected annotation issues from GitHub and print them
or save them as a tsv file.


Usage example:
    issues = get_issues("OpenITI/Annotation",
                        #issue_labels=["in progress"],
                        state="all"
                        )
    issues = define_text_uris(issues)
    uri_dict = sort_issues_by_uri(issues)
    print_issues_by_uri(uri_dict, "test.tsv")
"""

from github import Github
import re

URI_REGEX = r"\d{4}[A-Z][a-zA-Z]+(?:\.[A-Z][a-zA-Z]+)?(?:\.\w+-[a-z]{3}\d+)?"


def define_text_uris(issues, verbose=False):
    """Define which text uri the issue pertains to.
    Store the uri in the issue object (issue.uri).

    Args:
        issues (list): a list of github issue objects.
        verbose (bool): if verbose, print issues for which no uris were found.

    Returns:
        issues (list): the list of updated github issue objects
    """
    for issue in issues:
        if re.findall(URI_REGEX, issue.title):
            issue.uri = re.findall(URI_REGEX, issue.title)[0]
        elif re.findall("OLD URI.+?"+URI_REGEX, issue.body):
            issue.uri = re.findall("OLD URI.+?"+URI_REGEX, issue.body)[0]
        elif re.findall(URI_REGEX, issue.body):
            issue.uri = re.findall(URI_REGEX, issue.body)[0]
        elif issue.comments:
            for c in issue.get_comments():
                if re.findall(URI_REGEX, c.body):
                    issue.uri = re.findall(URI_REGEX, c.body)[0]
                    break
                issue.uri = ""
        else:
            issue.uri = ""
            if verbose:
                print("no uri found")
                print("    number:", issue.number)
                print("    title:", issue.title)
                print("    body:", issue.body)
                print("    comments:", [x.body for x in issue.get_comments()])
                input("Press enter to continue")
        #print("issue.uri:", issue.uri)
    return issues


def sort_issues_by_uri(issues):
    """Create a dictionary with the uris as keys.

    Args:
        issues (list): a list of github issue objects

    Returns:
        uri_dict (dict): a dictionary:
            key: uri
            value: list of github issue objects related to this uri
    """
    uri_dict = dict()
    for issue in issues:
        if issue.uri: # leave out issues for which we didn't find a URI
            if issue.uri in uri_dict:
                uri_dict[issue.uri].append(issue)
            else:
                uri_dict[issue.uri] = [issue]
    return uri_dict

def print_issues_by_uri(uri_dict, save_fp=""):
    """Print a tab-delimited list of uris with the issues connected to them.
    URI     Issue number    Issue label

    Args:
        uri_dict (dict): key: uri,
                         value: list of github issues related to this uri

    Returns:
        None
    """
    s = "{}\t{}\t{}\t{}\n".format("URI", "Issue number",
                                  "Issue label", "Issue state")
    for uri, issues in sorted(uri_dict.items()):
        for issue in issues:
            for label in issue.labels:
                s += "{}\t{}\t{}\t{}\n".format(uri, issue.number,
                                               label.name, issue.state)
    
    if save_fp:
        print("Saved list of issues to", save_fp)
        with open(save_fp, mode="w", encoding="utf-8") as file:
            file.write(s)
    else:
        print(s)


def get_issues(repo_name, #user=None, password=None,
               access_token="",
               issue_labels=None, state="open"):
    """Get all issues connected to a specific github repository.

    Args:
        repo_name (str): the name of the Github repository
        user (str): username
        password (str): password
        issue_labels (list; default: None): a list of github issue label names;
            only the issues with an issue label name in this
            list will be downloaded;
            if set to None, all issues will be downloaded
        state (str; default: "open"): only the issues with this state
            (open/closed/all) will be downloaded.

    Returns:
        issues (list): a list of github issues. 
    """
##    if user == None:
##        user = input("User: ")
##    if password == None:
##        password = input("Password: ")
##
##    g = Github(user, password)
    g = Github(access_token)
    print("logged in to GitHub to collect issues...")
    repo = g.get_repo(repo_name)
    print("issue labels in this repo ({}):".format(repo_name))
    for label in repo.get_labels():
        print("  ", label)
    print("getting relevant issues from GitHub...")
    for label in issue_labels:
        print("  ", label)
    if state:
        issues = repo.get_issues(state=state)
    else:
        issues = repo.get_issues(state="all")
    if issue_labels != None:
        filtered = []
        for i in issues:
            for il in issue_labels:
                if il in [label.name for label in i.labels]:
                    filtered.append(i)
                    break
        return filtered
    else:
        return issues


if __name__ == "__main__":
    issues = get_issues("OpenITI/Annotation",
                        #issue_labels=["in progress"],
                        state="all"
                        )
    issues = define_text_uris(issues)
    uri_dict = sort_issues_by_uri(issues)
    print_issues_by_uri(uri_dict, "test.tsv")
    


        
