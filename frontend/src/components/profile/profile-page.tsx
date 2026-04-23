'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ProfileAlertingCard from '@/components/profile/profile-alerting-card';
import ProfileCountryScopeCard from '@/components/profile/profile-country-scope-card';
import ProfileEmptyState from '@/components/profile/profile-empty-state';
import ProfileIndustryCard from '@/components/profile/profile-industry-card';
import ProfileIndustryScopeCard from '@/components/profile/profile-industry-scope-card';
import ProfileKeywordsCard from '@/components/profile/profile-keywords-card';
import ProfileMatchingExplainer from '@/components/profile/profile-matching-explainer';
import ProfilePageHeader from '@/components/profile/profile-page-header';
import ProfileSaveBar from '@/components/profile/profile-save-bar';
import { useMonitoringSetup } from '@/context/monitoring-setup-context';
import { useTranslation } from '@/context/language-context';
import { profileApi, type BusinessProfileWorkspaceResponse } from '@/lib/profile-api-adapter';
import type { NotificationPreferencesApiResponse } from '@/lib/notification-api-adapter';
import {
  areBusinessProfileFormsEqual,
  normalizeProfileKeywords,
  sanitizeIndustryLabel,
  validateBusinessProfileForm,
  validateKeywordInput,
  type BusinessProfileFormState,
} from '@/lib/profile-validation';

function toFormState(workspace: BusinessProfileWorkspaceResponse): BusinessProfileFormState {
  return {
    keywords: normalizeProfileKeywords(workspace.profile.keywords),
    countryCodes: workspace.profile.country_codes ?? [],
    industryCodes: workspace.profile.industry_codes ?? [],
    industryLabel: workspace.profile.industry_label ?? '',
    alertEnabled: workspace.profile.alert_enabled,
  };
}

const EMPTY_NOTIFICATION_PREFERENCES: NotificationPreferencesApiResponse = {
  user_id: '',
  email_enabled: true,
  whatsapp_enabled: false,
  whatsapp_phone_e164: null,
  daily_brief_enabled: true,
  instant_alert_enabled: false,
  preferred_language: 'auto',
};

export default function ProfilePage() {
  const { t } = useTranslation();
  const { monitoringActive, refreshMonitoringSetup } = useMonitoringSetup();
  const keywordInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [notificationPreferences, setNotificationPreferences] =
    useState<NotificationPreferencesApiResponse>(EMPTY_NOTIFICATION_PREFERENCES);
  const [form, setForm] = useState<BusinessProfileFormState>({
    keywords: [],
    countryCodes: [],
    industryCodes: [],
    industryLabel: '',
    alertEnabled: true,
  });
  const [initialForm, setInitialForm] = useState<BusinessProfileFormState>({
    keywords: [],
    countryCodes: [],
    industryCodes: [],
    industryLabel: '',
    alertEnabled: true,
  });
  const [keywordDraft, setKeywordDraft] = useState('');
  const [editingKeyword, setEditingKeyword] = useState<string | null>(null);
  const [keywordError, setKeywordError] = useState<string | null>(null);
  const [industryError, setIndustryError] = useState<string | null>(null);

  const validationMessages = t.profilePage.validation;

  const loadWorkspace = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const workspace = await profileApi.getWorkspace();
      const nextForm = toFormState(workspace);

      setNotificationPreferences(workspace.notificationPreferences);
      setForm(nextForm);
      setInitialForm(nextForm);
      setSaveError(null);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t.profilePage.errors.load);
    } finally {
      setLoading(false);
    }
  }, [t.profilePage.errors.load]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  useEffect(() => {
    if (!saveSuccess) {
      return;
    }

    const timeout = window.setTimeout(() => {
      setSaveSuccess(null);
    }, 3500);

    return () => window.clearTimeout(timeout);
  }, [saveSuccess]);

  const dirty = useMemo(
    () => !areBusinessProfileFormsEqual(form, initialForm),
    [form, initialForm]
  );

  const isFirstTime = form.keywords.length === 0;
  const saveBarVisible = dirty || saving || Boolean(saveError) || Boolean(saveSuccess);

  function focusKeywordInput() {
    keywordInputRef.current?.focus();
    keywordInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function commitKeyword() {
    const nextKeyword = keywordDraft.trim();
    const currentKeywords = editingKeyword
      ? form.keywords.filter((keyword) => keyword !== editingKeyword)
      : form.keywords;

    const nextError = validateKeywordInput(nextKeyword, currentKeywords, validationMessages, {
      skipDuplicateFor: editingKeyword,
    });

    if (nextError) {
      setKeywordError(nextError);
      return;
    }

    const nextKeywords = editingKeyword
      ? form.keywords.map((keyword) => (keyword === editingKeyword ? nextKeyword : keyword))
      : [...form.keywords, nextKeyword];

    setForm((current) => ({
      ...current,
      keywords: normalizeProfileKeywords(nextKeywords),
    }));
    setKeywordDraft('');
    setEditingKeyword(null);
    setKeywordError(null);
    setSaveError(null);
    setSaveSuccess(null);
  }

  function removeKeyword(keyword: string) {
    setForm((current) => ({
      ...current,
      keywords: current.keywords.filter((item) => item !== keyword),
    }));

    if (editingKeyword === keyword) {
      setEditingKeyword(null);
      setKeywordDraft('');
    }

    setKeywordError(null);
    setSaveSuccess(null);
  }

  function startEditKeyword(keyword: string) {
    setEditingKeyword(keyword);
    setKeywordDraft(keyword);
    setKeywordError(null);
    focusKeywordInput();
  }

  function resetEditing() {
    setEditingKeyword(null);
    setKeywordDraft('');
    setKeywordError(null);
  }

  function handleKeywordKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      commitKeyword();
    }
  }

  function handleReset() {
    setForm(initialForm);
    setKeywordDraft('');
    setEditingKeyword(null);
    setKeywordError(null);
    setIndustryError(null);
    setSaveError(null);
    setSaveSuccess(null);
  }

  async function handleSave() {
    const nextForm = {
      ...form,
      industryLabel: sanitizeIndustryLabel(form.industryLabel),
      keywords: normalizeProfileKeywords(form.keywords),
    };

    const validation = validateBusinessProfileForm(nextForm, validationMessages);
    setKeywordError(validation.keywords ?? null);
    setIndustryError(validation.industry ?? null);
    setSaveError(null);

    if (validation.keywords || validation.industry) {
      return;
    }

    setSaving(true);

    try {
      const savedProfile = await profileApi.updateProfile({
        keywords: nextForm.keywords,
        alert_enabled: nextForm.alertEnabled,
        country_codes: nextForm.countryCodes,
        industry_codes: nextForm.industryCodes,
        industry_label: nextForm.industryLabel || null,
      });

      const savedForm: BusinessProfileFormState = {
        keywords: normalizeProfileKeywords(savedProfile.keywords),
        countryCodes: savedProfile.country_codes ?? [],
        industryCodes: savedProfile.industry_codes ?? [],
        industryLabel: savedProfile.industry_label ?? '',
        alertEnabled: savedProfile.alert_enabled,
      };

      setForm(savedForm);
      setInitialForm(savedForm);
      setSaveSuccess(t.profilePage.saveBar.saved);
      await refreshMonitoringSetup();
    } catch (nextError) {
      setSaveError(nextError instanceof Error ? nextError.message : t.profilePage.errors.save);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8 min-h-screen">
        <div className="h-36 animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        <div className="grid gap-8 xl:grid-cols-12">
          <div className="space-y-8 xl:col-span-7">
            <div className="h-[320px] animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-[220px] animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
          </div>
          <div className="space-y-8 xl:col-span-5">
            <div className="h-[360px] animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-[320px] animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-6 min-h-screen">
        <ProfilePageHeader
          dirty={false}
          saving={false}
          monitoringActive={monitoringActive}
          saveError={null}
          saveSuccess={null}
          onSave={handleSave}
          onReset={handleReset}
        />
        <div className="rounded-[24px] border border-red-200 bg-red-50 p-6 dark:border-red-900/30 dark:bg-red-950/20">
          <p className="text-sm font-semibold text-red-700 dark:text-red-300">
            {error}
          </p>
          <p className="mt-2 text-sm leading-6 text-red-600 dark:text-red-400">
            {t.profilePage.errors.loadSupport}
          </p>
        </div>
        <div>
          <button
            type="button"
            onClick={() => void loadWorkspace()}
            className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            {t.profilePage.actions.retry}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8 min-h-screen">
      <ProfilePageHeader
        dirty={dirty}
        saving={saving}
        monitoringActive={monitoringActive}
        saveError={saveError}
        saveSuccess={saveSuccess}
        onSave={handleSave}
        onReset={handleReset}
      />

      {isFirstTime ? <ProfileEmptyState onPrimaryAction={focusKeywordInput} /> : null}

      <div className="grid gap-8 xl:grid-cols-12">
        <div className="space-y-8 xl:col-span-7">
          <ProfileKeywordsCard
            keywords={form.keywords}
            keywordDraft={keywordDraft}
            editingKeyword={editingKeyword}
            keywordError={keywordError}
            onDraftChange={(nextValue) => {
              setKeywordDraft(nextValue);
              setKeywordError(null);
              setSaveError(null);
              setSaveSuccess(null);
            }}
            onDraftKeyDown={handleKeywordKeyDown}
            onCommitKeyword={commitKeyword}
            onStartEditKeyword={startEditKeyword}
            onRemoveKeyword={removeKeyword}
            onCancelEdit={resetEditing}
            inputRef={keywordInputRef}
          />
          <ProfileIndustryCard
            value={form.industryLabel}
            error={industryError}
            onChange={(nextValue) => {
              setForm((current) => ({ ...current, industryLabel: nextValue }));
              setIndustryError(null);
              setSaveError(null);
              setSaveSuccess(null);
            }}
          />
          <ProfileCountryScopeCard
            countryCodes={form.countryCodes}
            onToggleCountry={(countryCode) => {
              setForm((current) => ({
                ...current,
                countryCodes: current.countryCodes.includes(countryCode)
                  ? current.countryCodes.filter((item) => item !== countryCode)
                  : [...current.countryCodes, countryCode],
              }));
              setSaveError(null);
              setSaveSuccess(null);
            }}
          />
          <ProfileIndustryScopeCard
            industryCodes={form.industryCodes}
            onToggleIndustry={(industryCode) => {
              setForm((current) => ({
                ...current,
                industryCodes: current.industryCodes.includes(industryCode)
                  ? current.industryCodes.filter((item) => item !== industryCode)
                  : [...current.industryCodes, industryCode],
              }));
              setSaveError(null);
              setSaveSuccess(null);
            }}
          />
        </div>

        <div className="space-y-8 xl:col-span-5">
          <ProfileAlertingCard
            alertEnabled={form.alertEnabled}
            notificationPreferences={notificationPreferences}
            onAlertEnabledChange={(nextValue) => {
              setForm((current) => ({ ...current, alertEnabled: nextValue }));
              setSaveError(null);
              setSaveSuccess(null);
            }}
          />
          <ProfileMatchingExplainer />
        </div>
      </div>

      <ProfileSaveBar
        visible={saveBarVisible}
        dirty={dirty}
        saving={saving}
        saveError={saveError}
        saveSuccess={saveSuccess}
        onSave={handleSave}
        onReset={handleReset}
      />
    </div>
  );
}
