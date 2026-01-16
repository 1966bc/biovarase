    <footer style="text-align: center; padding: 20px; color: #7f8c8d; font-size: 0.85rem; margin-top: 40px;">
        Biovarase &copy; <?= date('Y') ?> - Giuseppe Costanzi
    </footer>

    <?php if (isset($pageJS) && is_array($pageJS)): ?>
        <?php foreach ($pageJS as $js): ?>
    <script src="/biovarase/js/<?= $js ?>"></script>
        <?php endforeach; ?>
    <?php endif; ?>
</body>
</html>
