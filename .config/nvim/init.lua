-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  vim.fn.system({ "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git", "--branch=stable", lazypath })
end
vim.opt.rtp:prepend(lazypath)

vim.g.mapleader = " "
-- With `nvim /path/to/dir`, make that dir the cwd (live_grep searches cwd)
if vim.fn.argc() > 0 and vim.fn.isdirectory(vim.fn.argv(0)) == 1 then
  vim.cmd("cd " .. vim.fn.argv(0))
end
vim.keymap.set("n", "<leader>e", function()
  require("oil").toggle_float()
end, { desc = "Toggle Oil" })

require("lazy").setup({
  {
    "stevearc/oil.nvim",
    ---@module 'oil'
    ---@type oil.SetupOpts
    opts = { float = { border = "rounded" } },
    dependencies = { { "echasnovski/mini.icons", opts = {} } },
    lazy = false,
  },
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { { "nvim-lua/plenary.nvim" } },
    keys = {
      {
        "<leader>fg",
        function() require("telescope.builtin").live_grep() end,
        desc = "Grep (find string in files)",
      },
      {
        "<leader>ff",
        function() require("telescope.builtin").find_files() end,
        desc = "Find file by name",
      },
    },
  },
})
