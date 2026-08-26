'use strict';
function createUseFetch(React, AbortControllerImpl = AbortController) {
  const { useEffect, useState } = React;
  return function useFetch(url, fetcher) {
    const [state, setState] = useState({ data: null, error: null, loading: false });
    useEffect(() => {
      const controller = new AbortControllerImpl();
      let active = true;
      setState(prev => ({ ...prev, error: null, loading: true }));
      fetcher(url, { signal: controller.signal })
        .then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then(data => {
          if (!active) return;
          setState({ data, error: null, loading: false });
        })
        .catch(error => {
          if (!active) return;
          if (error?.name === 'AbortError') return;
          setState({ data: null, error, loading: false });
        });
      return () => { active = false; controller.abort(); };
    }, [url, fetcher]);
    return state;
  };
}
module.exports = { createUseFetch };
