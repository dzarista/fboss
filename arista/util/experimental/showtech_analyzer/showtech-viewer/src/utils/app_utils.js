// src/app_utils.js
export function removeFile(logs, selectedIndex, idxToRemove) {
  // remove that one:
  const newLogs = logs.filter((_, i) => i !== idxToRemove)

  // adjust selection:
  let newSelected = selectedIndex
  if (selectedIndex === idxToRemove) {
    newSelected = -1
  } else if (selectedIndex > idxToRemove) {
    newSelected = selectedIndex - 1
  }
  // else selectedIndex < idxToRemove → no change

  return { logs: newLogs, selectedIndex: newSelected }
}