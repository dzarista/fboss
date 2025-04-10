set -x

#### This script merges code from https://github.com/facebookexternal/fboss.bsp.arista
#### to Git subtree in https://github.com/aristanetworks/arista-fboss

repo_name=git@github.com:aristanetworks/arista-fboss.git
date_string=$(date +"%m-%d-%Y")
pr_title="pull fboss.bsp.arista to subtree in arista-fboss - ${date_string}"
pr_description="syncing https://github.com/facebookexternal/fboss.bsp.arista to fboss.bsp.arista subtree in https://github.com/aristanetworks/arista-fboss on ${date_string}"
# File attached in the status email
output_file=upstream_pull_status.txt
# Status email text
status_email_file=status_email_content.txt
# Status email subject
email_subject_file=status_email_subject.txt

# Setting up GitHub username and email
git config --local user.email "srv-fboss-arista@arista.com"
git config --local user.name "srv-fboss-arista-robot"

# Set up upstream branch
GIT_SSH_COMMAND="ssh -i private.key -o IdentitiesOnly=yes" git remote add bsp_upstream git@github.com:facebookexternal/fboss.bsp.arista.git
GIT_SSH_COMMAND="ssh -i private.key -o IdentitiesOnly=yes" git fetch bsp_upstream

# Check out a new branch which will be updated
branch_name="srv-fboss-arista-robot.bsp_pull_${date_string}"
if git ls-remote --exit-code --heads $repo_name $branch_name; then
   git push origin -d $branch_name
fi
git checkout -b $branch_name origin/main || exit 1

echo "fboss.bsp.arista pull: $date_string" > $email_subject_file

# Pull fboss.bsp.arista to subtree in the arista-fboss repository
# --squash option had to be used since the subtree was originally created with the --squash option
if GIT_SSH_COMMAND="ssh -i private.key -o IdentitiesOnly=yes" git subtree pull --prefix=fboss.bsp.arista bsp_upstream main --squash &> subtree_pull_status.txt; then
   auto_merge_successful=true
   if ! grep "Subtree is already at commit" subtree_pull_status.txt; then
      git push origin HEAD
      pr_link=$(gh pr create --title "$pr_title" --body "$pr_description" --head $branch_name --base main --repo $repo_name | grep https)
      echo "Created a pull request from branch $branch_name" > $output_file
      echo "Created the pull request $pr_link with all the upstream changes" > $status_email_file
   fi
else
   auto_merge_successful=false
   git status > git_status_output.txt
   git diff > git_diff_output.txt
   git merge --abort
fi

if [ "$auto_merge_successful" = false ] ; then
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
   echo "Couldn't create a pull request due to merge conflicts" > $status_email_file
fi

