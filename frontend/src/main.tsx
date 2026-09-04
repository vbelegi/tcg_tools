import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAdmin, RequireAuth, RequireStaff } from "./components/RequireAuth";
import { AcaoDetailPage } from "./pages/acoes/AcaoDetailPage";
import { AcaoNovaPage } from "./pages/acoes/AcaoNovaPage";
import { AcaoParticipacaoPage } from "./pages/acoes/AcaoParticipacaoPage";
import { AcoesListPage } from "./pages/acoes/AcoesListPage";
import { AgendaPage } from "./pages/AgendaPage";
import { AuditLogsPage } from "./pages/AuditLogsPage";
import { CalendarPage } from "./pages/CalendarPage";
import { ClaimInvitePage } from "./pages/ClaimInvitePage";
import { Home } from "./pages/Home";
import { LoginPage } from "./pages/LoginPage";
import { PlayerProfilePage } from "./pages/PlayerProfilePage";
import { PrivacidadePage } from "./pages/PrivacidadePage";
import { PremiacaoPage } from "./pages/premiacao/PremiacaoPage";
import { RankingPage } from "./pages/RankingPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { CancelEmailChangePage } from "./pages/CancelEmailChangePage";
import { ConfirmEmailChangePage } from "./pages/ConfirmEmailChangePage";
import { TermosPage } from "./pages/TermosPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { VerificarEmailContaPage } from "./pages/VerificarEmailContaPage";
import { SorteadorPage } from "./pages/sorteador/SorteadorPage";
import { TcgGamesPage } from "./pages/TcgGamesPage";
import { TorneioDetailPage } from "./pages/torneios/TorneioDetailPage";
import { TorneioColocacaoPage } from "./pages/torneios/TorneioColocacaoPage";
import { TorneioExternoPage } from "./pages/torneios/TorneioExternoPage";
import { TorneioNovoPage } from "./pages/torneios/TorneioNovoPage";
import { TorneioResultadoPage } from "./pages/torneios/TorneioResultadoPage";
import { TorneioDeckPage } from "./pages/torneios/TorneioDeckPage";
import { TorneioRodadaPage } from "./pages/torneios/TorneioRodadaPage";
import { TorneiosListPage } from "./pages/torneios/TorneiosListPage";
import { UsuariosPage } from "./pages/UsuariosPage";
import "./index.css";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/convite/:token" element={<ClaimInvitePage />} />
          <Route path="/redefinir-senha/:token" element={<ResetPasswordPage />} />
          <Route path="/verificar-email/:token" element={<VerifyEmailPage />} />
          <Route path="/confirmar-troca-email/:token" element={<ConfirmEmailChangePage />} />
          <Route path="/cancelar-troca-email/:token" element={<CancelEmailChangePage />} />
          <Route path="/esqueci-senha" element={<ForgotPasswordPage />} />
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="calendario" element={<CalendarPage />} />
            <Route path="ranking" element={<RankingPage />} />
            <Route path="jogadores/:id" element={<PlayerProfilePage />} />
            <Route path="acoes" element={<AcoesListPage />} />
            <Route element={<RequireStaff />}>
              <Route path="acoes/nova" element={<AcaoNovaPage />} />
            </Route>
            <Route path="acoes/participar/:token" element={<AcaoParticipacaoPage />} />
            <Route path="acoes/:id" element={<AcaoDetailPage />} />
            <Route path="torneios" element={<TorneiosListPage />} />
            <Route path="torneios/:id" element={<TorneioDetailPage />} />
            <Route path="torneios/:id/resultado" element={<TorneioResultadoPage />} />
            <Route path="torneios/:id/jogadores/:playerId/deck" element={<TorneioDeckPage />} />
            <Route path="conta/senha" element={<Navigate to="/" replace />} />
            <Route path="conta/verificar-email" element={<VerificarEmailContaPage />} />
            <Route path="termos" element={<TermosPage />} />
            <Route path="privacidade" element={<PrivacidadePage />} />
          </Route>
          <Route element={<RequireAuth />}>
            <Route element={<Layout />}>
              <Route path="torneios/:id/rodadas/:n" element={<TorneioRodadaPage />} />
            </Route>
          </Route>
          <Route element={<RequireStaff />}>
            <Route element={<Layout />}>
              <Route path="premiacao" element={<PremiacaoPage />} />
              <Route path="sorteador" element={<SorteadorPage />} />
              <Route path="agenda" element={<AgendaPage />} />
              <Route path="torneios/novo" element={<TorneioNovoPage />} />
              <Route path="torneios/:id/colocacoes" element={<TorneioColocacaoPage />} />
            </Route>
          </Route>
          <Route element={<RequireAdmin />}>
            <Route element={<Layout />}>
              <Route path="torneios/externo" element={<TorneioExternoPage />} />
              <Route path="usuarios" element={<UsuariosPage />} />
              <Route path="auditoria" element={<AuditLogsPage />} />
              <Route path="tcgs" element={<TcgGamesPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
