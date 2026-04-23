import { INDUSTRY_OPTIONS } from './industry-options';
import type { Language } from './translations';

const COUNTRY_LABELS: Record<string, { en: string; ar: string }> = {
  AE: { en: 'United Arab Emirates', ar: 'الإمارات العربية المتحدة' },
  SA: { en: 'Saudi Arabia', ar: 'المملكة العربية السعودية' },
  OM: { en: 'Oman', ar: 'سلطنة عُمان' },
  BH: { en: 'Bahrain', ar: 'البحرين' },
  QA: { en: 'Qatar', ar: 'قطر' },
};

const INDUSTRY_LABELS = Object.fromEntries(
  INDUSTRY_OPTIONS.map((option) => [option.code, option.label])
);

export type MatchReasonParts = {
  keywords: string[];
  countryCodes: string[];
  industryCodes: string[];
};

export function getCountryLabel(countryCode: string, lang: Language): string {
  return COUNTRY_LABELS[countryCode]?.[lang] ?? countryCode;
}

export function getIndustryLabel(industryCode: string): string {
  return INDUSTRY_LABELS[industryCode] ?? industryCode;
}

export function getMatchReasonBadges(
  reason: MatchReasonParts,
  lang: Language
): Array<{ key: string; label: string }> {
  return [
    ...reason.countryCodes.map((countryCode) => ({
      key: `country:${countryCode}`,
      label: getCountryLabel(countryCode, lang),
    })),
    ...reason.industryCodes.map((industryCode) => ({
      key: `industry:${industryCode}`,
      label: getIndustryLabel(industryCode),
    })),
    ...reason.keywords.map((keyword) => ({
      key: `keyword:${keyword}`,
      label: keyword,
    })),
  ];
}
