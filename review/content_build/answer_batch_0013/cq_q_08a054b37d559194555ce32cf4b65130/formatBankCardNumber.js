function formatBankCardNumber(digits) {
  if (typeof digits !== 'string' || !/^\d*$/.test(digits)) {
    throw new TypeError('bank card number must contain ASCII digits only');
  }
  return digits.replace(/(\d{4})(?=\d)/g, '$1 ');
}

module.exports = { formatBankCardNumber };
