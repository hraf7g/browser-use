'use client';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from '@/context/language-context';
import { Mail, MessageSquare, Zap, Clock } from 'lucide-react';
import NotificationChannelCard from './notification-channel-card';
import { motion } from 'framer-motion';
import { notificationBackendApi, type NotificationPreferencesApiResponse } from '@/lib/notification-api-adapter';
import { compactBadgeClass } from '@/lib/locale-ui';

type PreferenceFormState = Omit<NotificationPreferencesApiResponse, 'user_id'>;

export default function NotificationPreferencesPanel() {
  const { t, lang } = useTranslation();
  const loadPreferencesError = t.notifications.errors.loadPreferences;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [form, setForm] = useState<PreferenceFormState>({
    email_enabled: true,
    whatsapp_enabled: false,
    whatsapp_phone_e164: null,
    daily_brief_enabled: true,
    instant_alert_enabled: false,
    preferred_language: 'auto',
  });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    notificationBackendApi
      .getPreferences()
      .then((data) => {
        if (!cancelled) {
          setForm({
            email_enabled: data.email_enabled,
            whatsapp_enabled: data.whatsapp_enabled,
            whatsapp_phone_e164: data.whatsapp_phone_e164,
            daily_brief_enabled: data.daily_brief_enabled,
            instant_alert_enabled: data.instant_alert_enabled,
            preferred_language: data.preferred_language,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(loadPreferencesError);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [loadPreferencesError]);

  const languageOptions = useMemo(
    () => [
      { id: 'auto', label: t.notifications.preferences.langAuto },
      { id: 'en', label: lang === 'ar' ? 'الإنجليزية' : 'English' },
      { id: 'ar', label: lang === 'ar' ? 'العربية' : 'Arabic' },
    ] as const,
    [lang, t]
  );

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSavedMessage(null);
    try {
      const updated = await notificationBackendApi.updatePreferences(form);
      setForm({
        email_enabled: updated.email_enabled,
        whatsapp_enabled: updated.whatsapp_enabled,
        whatsapp_phone_e164: updated.whatsapp_phone_e164,
        daily_brief_enabled: updated.daily_brief_enabled,
        instant_alert_enabled: updated.instant_alert_enabled,
        preferred_language: updated.preferred_language,
      });
      setSavedMessage(t.notifications.preferences.saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : loadPreferencesError);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={index}
            className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
      {/* Channels Section */}
      <section>
        <h3 className={`mb-4 text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.preferences.channels}</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <NotificationChannelCard 
            icon={Mail}
            title={t.notifications.preferences.email}
            description={t.notifications.preferences.emailDesc}
            enabled={form.email_enabled}
            statusEnabledLabel={t.profilePage.alerting.enabled}
            statusDisabledLabel={t.profilePage.alerting.disabled}
            lang={lang}
          />
          <NotificationChannelCard 
            icon={MessageSquare}
            title={t.notifications.preferences.whatsapp}
            description={t.notifications.preferences.whatsappDesc}
            enabled={form.whatsapp_enabled}
            isInput
            placeholder="+966 5X XXX XXXX"
            value={form.whatsapp_phone_e164 ?? ''}
            onChange={(value) => setForm((current) => ({ ...current, whatsapp_phone_e164: value || null }))}
            statusEnabledLabel={t.profilePage.alerting.enabled}
            statusDisabledLabel={t.profilePage.alerting.disabled}
            lang={lang}
          />
        </div>
      </section>

      {/* Delivery Types Section */}
      <section>
        <h3 className={`mb-4 text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.preferences.types}</h3>
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 p-6 dark:border-slate-800">
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 flex items-center justify-center shrink-0">
                <Zap size={20} />
              </div>
              <div>
                <p className="font-bold text-slate-900 dark:text-white">{t.notifications.preferences.instant}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t.notifications.preferences.instantDesc}</p>
              </div>
            </div>
            <Switch checked={form.instant_alert_enabled} onChange={(checked) => setForm((current) => ({ ...current, instant_alert_enabled: checked }))} />
          </div>
          <div className="flex items-center justify-between p-6">
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-900/30 text-amber-600 flex items-center justify-center shrink-0">
                <Clock size={20} />
              </div>
              <div>
                <p className="font-bold text-slate-900 dark:text-white">{t.notifications.preferences.daily}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t.notifications.preferences.dailyDesc}</p>
              </div>
            </div>
            <Switch checked={form.daily_brief_enabled} onChange={(checked) => setForm((current) => ({ ...current, daily_brief_enabled: checked }))} />
          </div>
        </div>
      </section>

      {/* Language Section */}
      <section>
        <h3 className={`mb-4 text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.preferences.language}</h3>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap gap-3">
            {languageOptions.map((option) => (
              <button 
                key={option.id}
                type="button"
                onClick={() => setForm((current) => ({ ...current, preferred_language: option.id }))}
                className={`px-6 py-2 rounded-full text-sm font-bold border transition-all ${
                  form.preferred_language === option.id 
                  ? 'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-500/20' 
                  : 'bg-transparent border-slate-200 dark:border-slate-800 text-slate-600 hover:border-blue-600 hover:text-blue-600'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
          {error}
        </div>
      )}

      {savedMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 dark:border-emerald-900/30 dark:bg-emerald-950/20 dark:text-emerald-300">
          {savedMessage}
        </div>
      )}

      <div className="pt-4 flex justify-end">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-xl bg-slate-900 px-8 py-3 font-bold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900"
        >
          {saving ? t.profilePage.actions.saving : t.notifications.preferences.save}
        </button>
      </div>
    </div>
  );
}

// Minimal Premium Switch Primitive
function Switch({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label
      className={`relative inline-flex h-6 w-12 cursor-pointer items-center rounded-full transition-colors duration-200 outline-none ${
        checked ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-800'
      }`}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="sr-only"
      />
      <motion.div
        animate={{ x: checked ? 24 : 0 }}
        className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white shadow-sm"
      />
    </label>
  );
}
