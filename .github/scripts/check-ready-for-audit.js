/**
 * Check if PR changes contain "ready to review" or "ready for review" markers
 * in .codex/tasks files and add "auditable" label if found.
 * 
 * This script is designed to run in GitHub Actions context with @actions/github
 * and @actions/core packages available.
 */

module.exports = async ({ github, context, core }) => {
  const prNumber = context.payload.pull_request?.number;
  
  if (!prNumber) {
    core.info('Not a pull request event, skipping audit check');
    return;
  }

  core.info(`Checking PR #${prNumber} for "ready to review" markers...`);

  try {
    // Get list of files changed in the PR
    const { data: files } = await github.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      per_page: 100
    });

    core.info(`Found ${files.length} changed files in PR`);

    // Filter for .codex/tasks files
    const taskFiles = files.filter(file => 
      file.filename.startsWith('.codex/tasks/') && 
      file.filename.endsWith('.md') &&
      (file.status === 'added' || file.status === 'modified')
    );

    core.info(`Found ${taskFiles.length} task files changed: ${taskFiles.map(f => f.filename).join(', ')}`);

    if (taskFiles.length === 0) {
      core.info('No .codex/tasks/*.md files modified, skipping audit check');
      return;
    }

    // Check each task file for "ready to review" or "ready for review" marker
    let foundReadyMarker = false;
    const filesWithMarker = [];

    for (const file of taskFiles) {
      core.info(`Fetching content for ${file.filename}...`);
      
      try {
        // Get the file content from the PR branch
        const { data: content } = await github.rest.repos.getContent({
          owner: context.repo.owner,
          repo: context.repo.repo,
          path: file.filename,
          ref: context.payload.pull_request.head.sha
        });

        // Decode base64 content
        const fileContent = Buffer.from(content.content, 'base64').toString('utf-8');
        
        // Check for "ready to review" or "ready for review" (case insensitive)
        const hasReadyMarker = /ready\s+(to|for)\s+review/i.test(fileContent);
        
        if (hasReadyMarker) {
          core.info(`✓ Found "ready to review" marker in ${file.filename}`);
          foundReadyMarker = true;
          filesWithMarker.push(file.filename);
        } else {
          core.info(`✗ No "ready to review" marker in ${file.filename}`);
        }
      } catch (error) {
        core.warning(`Failed to fetch content for ${file.filename}: ${error.message}`);
      }
    }

    if (foundReadyMarker) {
      core.info(`Found "ready to review" in ${filesWithMarker.length} file(s): ${filesWithMarker.join(', ')}`);
      
      // Add "auditable" label to the PR
      try {
        await github.rest.issues.addLabels({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: prNumber,
          labels: ['auditable']
        });
        core.info('✓ Added "auditable" label to PR');
        
        // Post a comment to notify that audit will be triggered
        await github.rest.issues.createComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: prNumber,
          body: `🔍 Detected task file(s) ready for audit:\n${filesWithMarker.map(f => `- \`${f}\``).join('\n')}\n\nThe auto-audit workflow will run shortly. Please wait for the audit to complete before merging.`
        });
        core.info('✓ Posted notification comment on PR');
      } catch (error) {
        core.error(`Failed to add label or comment: ${error.message}`);
        throw error;
      }
    } else {
      core.info('No "ready to review" markers found in changed task files');
    }
  } catch (error) {
    core.setFailed(`Error checking for audit markers: ${error.message}`);
    throw error;
  }
};
