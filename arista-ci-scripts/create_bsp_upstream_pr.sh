set -x

#### This script creates a pull request in https://github.com/facebookexternal/fboss.bsp.arista
#### with the changes made to the Git subtree in https://github.com/aristanetworks/arista-fboss

repo_name=git@github.com:facebookexternal/fboss.bsp.arista.git
upstream_pr_branch_name="bsp_upstream_pr_${PR_BRANCH}"
pr_title="push subtree changes to fboss.bsp.arista"
pr_description="Upstream pull request with the changes to Git subtree from the branch ${PR_BRANCH}."
# File attached in the status email
output_file=upstream_pr_status.txt
# Status email text
status_email_file=status_email_content.txt
# Status email subject
email_subject_file=status_email_subject.txt

echo "fboss.bsp.arista pull request from $PR_BRANCH" > $email_subject_file

mkdir upstream_repo
cd upstream_repo
GIT_SSH_COMMAND="ssh -i ../private.key -o IdentitiesOnly=yes" git clone $repo_name
cd fboss.bsp.arista
if GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git ls-remote --exit-code --heads $repo_name $upstream_pr_branch_name; then
   GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git push origin -d $upstream_pr_branch_name
fi
GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git checkout -b $upstream_pr_branch_name origin/main || exit 1
cd ..
# We know the patch file will be non-empty (controlled by the workflow yml file)
if patch -p1 < ../subtree.patch &> patch_status.txt; then
   cd fboss.bsp.arista
   git config --global user.name "srv-fboss-arista"
   git config --global user.email "srv-fboss-arista@arista.com"
   GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git add -A
   GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git commit -m "upstreaming BSP changes"
   GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git push origin $upstream_pr_branch_name
   GIT_SSH_COMMAND="ssh -i ../../private.key -o IdentitiesOnly=yes" git checkout main || exit 1
   pr_link=$(gh pr create --title "$pr_title" --body "$pr_description" --head $upstream_pr_branch_name --base main --repo $repo_name --draft | grep https)
   cd ../..
   echo "Created a pull request from branch $upstream_pr_branch_name." > $output_file
   echo "Created the draft pull request $pr_link with all the changes in BSP subtree. Please publish the pull request after updating the title and description." > $status_email_file
else
   cd ..
   echo "Couldn't create a pull request due to merge conflicts." > $status_email_file
   echo "Details of the merge conflicts" >> $output_file
   echo "==============================" >> $output_file
   cat upstream_repo/patch_status.txt >> $output_file
fi
