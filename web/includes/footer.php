    <footer style="text-align: center; padding: 20px; color: var(--text-secondary, #7f8c8d); font-size: 0.85rem; margin-top: 40px; background: var(--bg-secondary, #fff); border-top: 1px solid var(--border-light, #ecf0f1);">
        <?php
        $siteName = getWorkingSiteName();
        if ($siteName): ?>
        <strong><?= htmlspecialchars($siteName) ?></strong> &mdash;
        <?php endif; ?>
        Biovarase &copy; <?= date('Y') ?>
    </footer>

    <?php if (isset($pageJS) && is_array($pageJS)): ?>
        <?php foreach ($pageJS as $js): ?>
    <script src="/biovarase/js/<?= $js ?>"></script>
        <?php endforeach; ?>
    <?php endif; ?>
</body>
</html>
