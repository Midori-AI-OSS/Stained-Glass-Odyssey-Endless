export function mergeUpgradePayload(previousData, result) {
  const base = { ...(previousData || {}) };
  if (result && typeof result === 'object') {
    Object.assign(base, result);
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'items')) {
    base.items = result.items || {};
  } else if (previousData && Object.prototype.hasOwnProperty.call(previousData, 'items')) {
    base.items = previousData.items;
  } else if (!base.items) {
    base.items = {};
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'total_points')) {
    base.total_points = result.total_points;
  } else if (previousData && Object.prototype.hasOwnProperty.call(previousData, 'total_points')) {
    base.total_points = previousData.total_points;
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'upgrade_points')) {
    base.upgrade_points = result.upgrade_points;
  } else if (previousData && Object.prototype.hasOwnProperty.call(previousData, 'upgrade_points')) {
    base.upgrade_points = previousData.upgrade_points;
  } else if (base.total_points != null && !Object.prototype.hasOwnProperty.call(base, 'upgrade_points')) {
    base.upgrade_points = base.total_points;
  }

  return base;
}

export function shouldRefreshRoster(result) {
  return !(result && Object.prototype.hasOwnProperty.call(result, 'items'));
}
