# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from lxml import etree
from contextlib import contextmanager
from openerp import api, fields, models
from openerp.addons.runbot.runbot import run, mkdirs


class RunbotBuild(models.Model):
    _inherit = 'runbot.build'

    coverage = fields.Float('Coverage', digits=(10, 2))

    @api.model
    def job_20_test_all(self, build, lock_path, log_path):
        if build.repo_id.use_coverage:
            # coverage behaves weirdly with very long path names
            # as the ones generated by repo names
            with build._chdir():
                return super(RunbotBuild, self).job_20_test_all(
                    build.with_context(runbot_coverage=True),
                    lock_path, log_path
                )
        return super(RunbotBuild, self).job_20_test_all(
            build, lock_path, log_path
        )

    @api.model
    def job_21_coverage(self, build, lock_path, log_path):
        if not build.repo_id.use_coverage:
            return
        output = build.path('logs/job_21_coverage')
        mkdirs([output])
        result = None
        with build._chdir():
            result = run(
                build.repo_id._coverage_command(
                    'html', '--directory', output, '--title', build.name
                )
            )
        if result:
            build.write({
                'result': 'ko',
            })
            build.github_status()
        output = os.path.join(output, 'index.html')
        if os.path.exists(output):
            doc = etree.fromstring(open(output).read(), etree.HTMLParser())
            coverage = 0.0
            for node in doc.xpath("//tr[@class='total']/td[@data-ratio]"):
                covered_lines, all_lines = node.get('data-ratio').split()
                coverage = float(covered_lines or 0) / float(all_lines or 1)
            build.write({
                'coverage': coverage,
            })
        return result

    @api.multi
    def cmd(self):
        cmd, modules = super(RunbotBuild, self).cmd()
        if self.env.context.get('runbot_coverage'):
            cmd = self.repo_id._coverage_command('run') + sum(
                (
                    list(t)
                    for t in
                    zip(
                        ['--source'] * len(modules.split(',')),
                        map(
                            lambda x: self.path('openerp/addons', x),
                            modules.split(','),
                        ),
                    )
                ),
                []
            ) + cmd[1:]
        return cmd, modules

    @contextmanager
    @api.multi
    def _chdir(self, *args):
        """Change the current directory, and change back afterwards"""
        self.ensure_one()
        current_dir = os.getcwd()
        os.chdir(self.path(*args))
        try:
            yield
        finally:
            os.chdir(current_dir)
