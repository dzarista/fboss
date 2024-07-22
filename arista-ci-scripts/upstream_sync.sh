set -x

#### This script merges code from https://github.com/facebook/fboss
#### to https://github.com/aristanetworks/arista-fboss

repo_name=git@github.com:aristanetworks/arista-fboss.git
date_string=$(date +"%m-%d-%Y")
pr_title="arista-fboss upstream sync ${date_string}"
pr_description="syncing https://github.com/aristanetworks/arista-fboss to https://github.com/facebook/fboss on ${date_string}"
output_file=upstream_sync_status.txt
status_email_file=status_email_file.txt

# Setting up github username and email
git config --local user.email "srv-fboss-arista@arista.com";
git config --local user.name  "srv-fboss-arista-robot";

# Set up upstream branch
git remote add upstream git@github.com:facebook/fboss.git
git fetch upstream

# Check out a new branch which will be updated
branch_name="srv-fboss-arista-robot.upstream_${date_string}"
if git ls-remote --exit-code --heads $repo_name $branch_name; then
   git push origin -d $branch_name
fi
git checkout -b $branch_name origin/main || exit 1

# Merges upstream branch and its associated develpment history into main branch
# --no-edit option is used to supress editing the auto-generated merge message
if git merge --no-edit upstream/main; then
   auto_merge_successful=true
   git push origin HEAD
   gh pr create --title "$pr_title" --body "$pr_description" --head $branch_name --base main --repo $repo_name
   echo "Created a pull request from branch $branch_name" > $output_file
   echo "Created the pull request $pr_title with all the upstream changes" > $status_email_file
else
   auto_merge_successful=false
   git status > git_status_output.txt
   git diff > git_diff_output.txt
   git merge --abort
fi

if [ "$auto_merge_successful" = false ] ; then
   if git merge --no-edit upstream/main --strategy-option ours; then
      git push origin HEAD
      gh pr create --title "$pr_title" --body "$pr_description" --head $branch_name --base main --repo $repo_name
      echo "Created a pull request from branch $branch_name. However some of the upstream changes were not pulled due to merge conflicts." > $output_file
      # Display any merge conficts which were not resolved
      echo "The following files had merge conflicts:" >> $output_file
      echo "========================================" >> $output_file
      grep 'both modified:' git_status_output.txt | sed $line -n -e 's/^.*both modified: //p' | while read -r line ; do
         echo $line >> $output_file
      done
      echo $'\n' >> $output_file
      echo "Details of the merge conflicts" >> $output_file
      echo "==============================" >> $output_file
      cat git_diff_output.txt >> $output_file
      echo "Created the pull request $pr_title after excluding some upstream changes. Please see the attached file to analyze the excluded files." > $status_email_file
   else
      echo "Encountered merge conflict which cannot be handled. Aborting further execution. See the logs below for more information" > $output_file
      # Displays merge confict details
      echo "git status" >> $output_file
      echo "==========" >> $output_file
      cat git_status_output.txt >> $output_file
      echo $'\n' >> $output_file
      echo "git diff" >> $output_file
      echo "========" >> $output_file
      cat git_diff_output.txt >> $output_file
      echo "Could not create a pull request with the upstream changes. Please see the attached file for more details." > $status_email_file
   fi
   exit -1
fi

