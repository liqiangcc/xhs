'use strict';

const DEFAULT_TIME_ZONE = 'Asia/Shanghai';

function currentDateString(options = {}) {
    const timeZone = options.timeZone || process.env.XHS_TIME_ZONE || DEFAULT_TIME_ZONE;
    const now = options.now || new Date();
    const parts = new Intl.DateTimeFormat('en-CA', {
        timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).formatToParts(now);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
}

function defaultDate(options = {}) {
    return options.date
        || options.buildDate
        || process.env.XHS_REVIEW_DATE
        || process.env.XHS_BUILD_DATE
        || currentDateString(options);
}

module.exports = {
    DEFAULT_TIME_ZONE,
    currentDateString,
    defaultDate,
};
