import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { api } from "../api/client.js";

export const seedDemoData = createAsyncThunk("crm/seedDemoData", api.seedDemoData);
export const fetchHcps = createAsyncThunk("crm/fetchHcps", api.getHcps);
export const fetchInteractions = createAsyncThunk("crm/fetchInteractions", api.getInteractions);

export const createInteraction = createAsyncThunk(
  "crm/createInteraction",
  async (payload, { getState }) => {
    const { selectedHcpId } = getState().crm;
    return api.createInteraction({ ...payload, hcp_id: selectedHcpId });
  },
);

export const chatAgent = createAsyncThunk("crm/chatAgent", async (message, { getState }) => {
  const { selectedHcpId, chatMessages } = getState().crm;
  return api.chatAgent({
    hcp_id: selectedHcpId,
    message,
    conversation: chatMessages.slice(-8),
  });
});

export const updateLatestInteraction = createAsyncThunk(
  "crm/updateLatestInteraction",
  async (payload, { getState }) => {
    const latest = getState().crm.interactions[0];
    if (!latest) {
      throw new Error("No interaction is available to edit.");
    }
    return api.updateInteraction(latest.id, payload);
  },
);

const initialState = {
  hcps: [],
  selectedHcpId: null,
  interactions: [],
  chatMessages: [
    {
      role: "assistant",
      content: "Select an HCP, then log an interaction by form or chat.",
    },
  ],
  toolEvents: [],
  suggestions: [],
  loading: false,
  saving: false,
  error: null,
};

const crmSlice = createSlice({
  name: "crm",
  initialState,
  reducers: {
    selectHcp(state, action) {
      state.selectedHcpId = action.payload;
      state.interactions = [];
      state.suggestions = [];
      state.toolEvents = [];
      state.chatMessages = [
        {
          role: "assistant",
          content: "Ready. You can use the structured form or tell the CRM copilot what happened.",
        },
      ];
    },
    addUserChatMessage(state, action) {
      state.chatMessages.push({ role: "user", content: action.payload });
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(seedDemoData.pending, startLoading)
      .addCase(seedDemoData.fulfilled, receiveHcps)
      .addCase(seedDemoData.rejected, receiveError)
      .addCase(fetchHcps.pending, startLoading)
      .addCase(fetchHcps.fulfilled, receiveHcps)
      .addCase(fetchHcps.rejected, receiveError)
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload;
      })
      .addCase(fetchInteractions.rejected, receiveError)
      .addCase(createInteraction.pending, startSaving)
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.saving = false;
        upsertInteraction(state, action.payload);
        state.toolEvents = [
          {
            name: "log_interaction",
            status: "ok",
            payload: { interaction_id: action.payload.id },
          },
        ];
        state.suggestions = action.payload.next_steps ?? [];
      })
      .addCase(createInteraction.rejected, receiveError)
      .addCase(updateLatestInteraction.pending, startSaving)
      .addCase(updateLatestInteraction.fulfilled, (state, action) => {
        state.saving = false;
        upsertInteraction(state, action.payload);
        state.toolEvents = [
          {
            name: "edit_interaction",
            status: "ok",
            payload: { interaction_id: action.payload.id },
          },
        ];
      })
      .addCase(updateLatestInteraction.rejected, receiveError)
      .addCase(chatAgent.pending, startSaving)
      .addCase(chatAgent.fulfilled, (state, action) => {
        state.saving = false;
        state.chatMessages.push({
          role: "assistant",
          content: action.payload.reply,
        });
        state.toolEvents = action.payload.tool_events ?? [];
        state.suggestions = action.payload.suggestions ?? [];
        if (action.payload.draft_interaction) {
          upsertInteraction(state, action.payload.draft_interaction);
        }
      })
      .addCase(chatAgent.rejected, receiveError);
  },
});

function startLoading(state) {
  state.loading = true;
  state.error = null;
}

function startSaving(state) {
  state.saving = true;
  state.error = null;
}

function receiveHcps(state, action) {
  state.loading = false;
  state.hcps = action.payload;
  if (!state.selectedHcpId && action.payload.length > 0) {
    state.selectedHcpId = action.payload[0].id;
  }
}

function receiveError(state, action) {
  state.loading = false;
  state.saving = false;
  state.error = action.error?.message ?? "Something went wrong.";
}

function upsertInteraction(state, interaction) {
  state.interactions = [
    interaction,
    ...state.interactions.filter((item) => item.id !== interaction.id),
  ];
}

export const { addUserChatMessage, clearError, selectHcp } = crmSlice.actions;
export default crmSlice.reducer;
