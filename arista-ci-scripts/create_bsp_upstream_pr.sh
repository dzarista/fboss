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

SCRIPT_START_DIR=$(pwd)

mkdir upstream_repo
cd upstream_repo
GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git clone $repo_name
cd fboss.bsp.arista
if GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git ls-remote --exit-code --heads $repo_name $upstream_pr_branch_name; then
   GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git push origin -d $upstream_pr_branch_name
fi
GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git checkout -b $upstream_pr_branch_name origin/main || exit 1
cd "${SCRIPT_START_DIR}/upstream_repo"
# Real text diff is found in text_only.patch. They can be applied in upstream_repo with 'patch' command
if patch -p1 < ${SCRIPT_START_DIR}/text_only.patch &> patch_status.txt; then
   cd "${SCRIPT_START_DIR}"
   # Binary file diff is found in binary_only.diff. 'patch' command doesn't work in the case of binary files.
   # Hence, process them one after the other.
   while read -r old_file modified_file; do
      # 'new_path' is the binary file path in 'upstream_repo'
      new_path="${old_file/#premerge/upstream_repo}"
      # If the updated binary file is found in 'original' copy, it's the version which we want to keep - copy it to the 'upstream_repo'
      # Otherwise it was deleted. Delete the file from the 'upstream repo'
      if [ -e "$modified_file" ]; then
         cp $modified_file $new_path
      else
         rm $new_path
      fi
   # binary_only.diff will have lines in the format "Binary files path_to_file1/file1 and path_to_file2/file2 differ"
   done < <(awk '{print $3, $5}' binary_only.diff)
   cd upstream_repo/fboss.bsp.arista
   git config --global user.name "srv-fboss-arista"
   git config --global user.email "srv-fboss-arista@arista.com"
   GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git add -A
   GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git commit -m "upstreaming BSP changes"
   GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git push origin $upstream_pr_branch_name
   GIT_SSH_COMMAND="ssh -i ${SCRIPT_START_DIR}/private.key -o IdentitiesOnly=yes" git checkout main || exit 1
   pr_link=$(gh pr create --title "$pr_title" --body "$pr_description" --head $upstream_pr_branch_name --base main --repo $repo_name --draft | grep https)
   cd "${SCRIPT_START_DIR}"
   echo "Created a pull request from branch $upstream_pr_branch_name." > $output_file
   echo "Created the draft pull request $pr_link with all the changes in BSP subtree. Make sure the pull request matches with the changes to the subtree. Please publish the pull request after updating the title and description." > $status_email_file
else
   cd "${SCRIPT_START_DIR}"
   echo "Couldn't create a pull request due to merge conflicts." > $status_email_file
   echo "Details of the merge conflicts" >> $output_file
   echo "==============================" >> $output_file
   cat upstream_repo/patch_status.txt >> $output_file
fi
