'use strict';

function createUseFetch(React) {
  const { useEffect, useState } = React;
  return function useFetch(request, params) {
    const [state, setState] = useState({ data: null, error: null, loading: false });

    useEffect(() => {
      const controller = new AbortController();
      let active = true;

      setState(prev => ({ ...prev, error: null, loading: true }));

      request(params, { signal: controller.signal })
        .then(data => {
          if (!active) return;
          setState({ data, error: null, loading: false });
        })
        .catch(error => {
          if (!active) return;
          if (error?.name === 'AbortError') return;
          setState({ data: null, error, loading: false });
        });

      return () => {
        active = false;
        controller.abort();
      };
    }, [request, params]);

    return state;
  };
}

module.exports = { createUseFetch };
