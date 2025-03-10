require("dotenv").config();
const { Client, GatewayIntentBits, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, Events, SlashCommandBuilder, Collection, PermissionsBitField } = require("discord.js");
const axios = require("axios");
const db = require("quick.db");

const TOKEN = process.env.BOT_TOKEN;

const client = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildMembers]
});

client.commands = new Collection();

/**
 * Slash Command to Set Seller Key
 */
client.commands.set("setsellerkey", {
    data: new SlashCommandBuilder()
        .setName("setsellerkey")
        .setDescription("Set the KeyAuth seller key for this server.")
        .addStringOption(option => option.setName("key").setDescription("Your KeyAuth seller key").setRequired(true)),
    async execute(interaction) {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
            return interaction.reply({ content: "🚫 You need Administrator permissions to use this command.", ephemeral: true });
        }

        const sellerKey = interaction.options.getString("key");
        db.set(`sellerkey_${interaction.guild.id}`, sellerKey);
        await interaction.reply({ content: "✅ Seller Key set successfully for this server!", ephemeral: true });
    }
});

/**
 * Slash Command to Send Reset Embed with @everyone
 */
client.commands.set("sendresetembed", {
    data: new SlashCommandBuilder()
        .setName("sendresetembed")
        .setDescription("Send an embed for users to reset their license keys.")
        .addStringOption(option => option.setName("message").setDescription("Custom message to display").setRequired(true)),
    async execute(interaction) {
        const sellerKey = db.get(`sellerkey_${interaction.guild.id}`);
        if (!sellerKey) {
            return interaction.reply({ content: "⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral: true });
        }

        const customMessage = interaction.options.getString("message");

        const embed = new EmbedBuilder()
            .setTitle("🔄 License Key Reset")
            .setDescription(`${customMessage}\n\nClick the button below to reset your KeyAuth license key.\n\n**@everyone @here**`)
            .setColor("#0099ff")
            .setFooter({ text: "© 2025 RAPIDFIRE - All Rights Reserved" });

        const button = new ButtonBuilder()
            .setCustomId("reset_license")
            .setLabel("Reset License")
            .setStyle(ButtonStyle.Success);

        const row = new ActionRowBuilder().addComponents(button);
        await interaction.reply({ content: "@everyone @here", embeds: [embed], components: [row] });
    }
});

/**
 * Handle Button Interactions for License Reset
 */
client.on(Events.InteractionCreate, async interaction => {
    if (!interaction.isButton()) return;

    const sellerKey = db.get(`sellerkey_${interaction.guild.id}`);
    if (!sellerKey) {
        return interaction.reply({ content: "⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral: true });
    }

    await interaction.reply({ content: "🔑 Please enter your license key:", ephemeral: true });

    const filter = msg => msg.author.id === interaction.user.id && msg.channelId === interaction.channelId;
    const collector = interaction.channel.createMessageCollector({ filter, time: 60000, max: 1 });

    collector.on("collect", async msg => {
        const licenseKey = msg.content.trim();
        const apiUrl = `https://keyauth.win/api/seller/?sellerkey=${sellerKey}&type=resetuser&user=${licenseKey}`;

        try {
            const response = await axios.get(apiUrl);
            if (response.status === 200 && response.data.success) {
                await interaction.followUp({ content: `✅ License **${licenseKey}** has been reset!`, ephemeral: true });
            } else {
                await interaction.followUp({ content: "❌ Failed to reset the key. Check your input.", ephemeral: true });
            }
        } catch (error) {
            await interaction.followUp({ content: "⚠️ Error contacting KeyAuth API.", ephemeral: true });
        }

        msg.delete();
    });

    collector.on("end", collected => {
        if (collected.size === 0) {
            interaction.followUp({ content: "⏳ Timeout! Try again.", ephemeral: true });
        }
    });
});

client.once(Events.ClientReady, async () => {
    console.log(`✅ Logged in as ${client.user.tag}`);
    try {
        const commands = client.commands.map(cmd => cmd.data);
        await client.application.commands.set(commands);
        console.log("✅ Slash Commands Registered!");
    } catch (error) {
        console.error("❌ Error Registering Slash Commands:", error);
    }
});

// Start bot
client.login(TOKEN);
