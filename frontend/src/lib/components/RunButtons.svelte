<script context="module">
  /*
   * RunButtons.svelte (module)
   *
   * Exports `buildRunMenu` which returns the main menu actions for the
   * right-hand panel on the home screen. Items include Run, Party, Warp,
   * Settings, Feedback, and Inventory. The Player Editor entry was removed
   * in favor of showing a slim editor inline within the Party Picker stats.
   *
   * Plans:
   * - Consider a contextual entry that jumps to the Party Picker with the
   *   player pre-selected once the per-character upgrade flow is ready.
   */
  import { Play, Users, PackageOpen, Settings, MessageSquare, Package } from 'lucide-svelte';

  // Build the run menu items array. Handlers are functions for each action.
  export function buildRunMenu(handlers, battleActive) {
    return [
      { icon: Play, label: 'Run', action: handlers.openRun, disabled: false },
      { icon: Users, label: 'Party', action: handlers.handleParty, disabled: battleActive },
      // Player Editor removed from main menu per design
      { icon: PackageOpen, label: 'Warp', action: handlers.openPulls, disabled: battleActive },
      { icon: Package, label: 'Inventory', action: handlers.openInventory, disabled: false },
      { icon: Settings, label: 'Settings', action: handlers.openSettings, disabled: false },
      { icon: MessageSquare, label: 'Feedback', action: handlers.openFeedback, disabled: false },
      // Inventory moved to in-run NavBar; remove from main menu
    ];
  }
</script>
