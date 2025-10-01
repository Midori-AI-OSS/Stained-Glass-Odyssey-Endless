export function getReviewKeyTransition({ reviewOpen, reviewKey, lastKey }) {
  if (!reviewOpen) {
    return {
      open: false,
      nextKey: null,
      shouldFetch: false,
      shouldReset: lastKey !== null,
      clearedKey: lastKey
    };
  }

  const changed = reviewKey !== lastKey;
  return {
    open: true,
    nextKey: reviewKey,
    shouldFetch: changed,
    shouldReset: changed,
    clearedKey: null
  };
}
