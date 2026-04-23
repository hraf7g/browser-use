const KEYWORD_LIMIT = 50;
const KEYWORD_MAX_LENGTH = 100;
const INDUSTRY_MAX_LENGTH = 120;

export type ProfileValidationMessages = {
  keywordRequired: string;
  keywordTooLong: string;
  keywordDuplicate: string;
  keywordLimit: string;
  industryTooLong: string;
};

export type BusinessProfileFormState = {
  keywords: string[];
  countryCodes: string[];
  industryCodes: string[];
  industryLabel: string;
  alertEnabled: boolean;
};

export function normalizeProfileKeywords(keywords: string[]): string[] {
  const nextKeywords: string[] = [];
  const seen = new Set<string>();

  for (const keyword of keywords) {
    const cleaned = keyword.trim();
    if (!cleaned) {
      continue;
    }

    const dedupeKey = cleaned.toLocaleLowerCase();
    if (seen.has(dedupeKey)) {
      continue;
    }

    seen.add(dedupeKey);
    nextKeywords.push(cleaned);
  }

  return nextKeywords.slice(0, KEYWORD_LIMIT);
}

export function validateKeywordInput(
  value: string,
  currentKeywords: string[],
  messages: ProfileValidationMessages,
  options?: { skipDuplicateFor?: string | null }
): string | null {
  const cleaned = value.trim();

  if (!cleaned) {
    return messages.keywordRequired;
  }

  if (cleaned.length > KEYWORD_MAX_LENGTH) {
    return messages.keywordTooLong;
  }

  const duplicate = currentKeywords.some((keyword) => {
    if (options?.skipDuplicateFor && keyword === options.skipDuplicateFor) {
      return false;
    }

    return keyword.localeCompare(cleaned, undefined, { sensitivity: 'accent' }) === 0;
  });

  if (duplicate) {
    return messages.keywordDuplicate;
  }

  if (currentKeywords.length >= KEYWORD_LIMIT) {
    return messages.keywordLimit;
  }

  return null;
}

export function sanitizeIndustryLabel(value: string): string {
  return value.trim().slice(0, INDUSTRY_MAX_LENGTH);
}

export function validateBusinessProfileForm(
  form: BusinessProfileFormState,
  messages: ProfileValidationMessages
): { keywords?: string; industry?: string } {
  const errors: { keywords?: string; industry?: string } = {};

  if (normalizeProfileKeywords(form.keywords).length === 0) {
    errors.keywords = messages.keywordRequired;
  }

  if (form.industryLabel.trim().length > INDUSTRY_MAX_LENGTH) {
    errors.industry = messages.industryTooLong;
  }

  return errors;
}

export function areBusinessProfileFormsEqual(
  left: BusinessProfileFormState,
  right: BusinessProfileFormState
): boolean {
  if (left.alertEnabled !== right.alertEnabled) {
    return false;
  }

  if (sanitizeIndustryLabel(left.industryLabel) !== sanitizeIndustryLabel(right.industryLabel)) {
    return false;
  }

  if (left.countryCodes.length !== right.countryCodes.length) {
    return false;
  }

  if (!left.countryCodes.every((countryCode, index) => countryCode === right.countryCodes[index])) {
    return false;
  }

  if (left.industryCodes.length !== right.industryCodes.length) {
    return false;
  }

  if (!left.industryCodes.every((industryCode, index) => industryCode === right.industryCodes[index])) {
    return false;
  }

  const leftKeywords = normalizeProfileKeywords(left.keywords);
  const rightKeywords = normalizeProfileKeywords(right.keywords);

  if (leftKeywords.length !== rightKeywords.length) {
    return false;
  }

  return leftKeywords.every((keyword, index) => keyword === rightKeywords[index]);
}

export { INDUSTRY_MAX_LENGTH, KEYWORD_LIMIT, KEYWORD_MAX_LENGTH };
